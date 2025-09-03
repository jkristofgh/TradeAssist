"""
Data Ingestion Service.

Handles real-time market data ingestion from Schwab API with data normalization,
validation, and storage in SQLite database with sub-second processing targets.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

import structlog
from sqlalchemy import select, update

from ..config import settings, get_all_instruments
from ..database.connection import get_db_session
from ..database.decorators import with_db_session, handle_db_errors
from ..integrations.schwab_client import SchwabRealTimeClient, SchwabAPIError
from ..models.instruments import Instrument, InstrumentStatus
from ..models.market_data import MarketData
from ..websocket.realtime import get_websocket_manager

logger = structlog.get_logger()


class DataNormalizer:
    """
    Market data normalization and validation.
    
    Converts raw Schwab API data to standardized format for database storage
    and alert processing with data validation and error handling.
    """
    
    @staticmethod
    def normalize_tick_data(symbol: str, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize raw tick data from Schwab API via schwab-package.
        
        Args:
            symbol: Instrument symbol.
            raw_data: Raw data from schwab-package (nested structure with 'content' array).
        
        Returns:
            Optional[Dict]: Normalized tick data or None if invalid.
        """
        try:
            # Log the raw data for debugging
            logger.debug(f"Normalizing data for {symbol}: {raw_data}")
            
            # Extract market data from schwab-package structure
            # Data comes as: {'service': '...', 'content': [{'key': symbol, 'FIELD': value, ...}]}
            content = raw_data.get('content', [])
            if not content:
                logger.warning(f"No content in data for {symbol}: {raw_data}")
                return None
            
            # Find the data for our symbol in the content array
            market_data = None
            for item in content:
                if item.get('key') == symbol:
                    market_data = item
                    break
            
            if not market_data:
                logger.warning(f"Symbol {symbol} not found in content: {content}")
                return None
            
            logger.debug(f"Found market data for {symbol}: {market_data}")
            
            # Extract common fields (adapted for Schwab schwab-package format)
            normalized = {
                "symbol": symbol.upper(),
                "timestamp": datetime.utcnow(),  # Use server time for now
                "price": None,
                "volume": None,
                "bid": None,
                "ask": None,
                "bid_size": None,
                "ask_size": None,
                "open_price": None,
                "high_price": None,
                "low_price": None,
            }
            
            # Map Schwab schwab-package fields to normalized fields
            # Based on actual streaming data structure from schwab-package
            field_mapping = {
                # Price fields
                "LAST_PRICE": "price",
                "lastPrice": "price",
                "last": "price",
                "price": "price",
                
                # Volume fields
                "TOTAL_VOLUME": "volume", 
                "volume": "volume",
                "vol": "volume",
                
                # Bid/Ask fields
                "BID_PRICE": "bid",
                "bid": "bid",
                "bidPrice": "bid",
                "ASK_PRICE": "ask",
                "ask": "ask", 
                "askPrice": "ask",
                
                # Size fields
                "BID_SIZE": "bid_size",
                "bidSize": "bid_size",
                "ASK_SIZE": "ask_size",
                "askSize": "ask_size",
                
                # OHLC fields
                "OPEN_PRICE": "open_price",
                "open": "open_price",
                "openPrice": "open_price",
                "HIGH_PRICE": "high_price", 
                "high": "high_price",
                "highPrice": "high_price",
                "LOW_PRICE": "low_price",
                "low": "low_price", 
                "lowPrice": "low_price",
            }
            
            # Apply field mapping
            for schwab_field, normalized_field in field_mapping.items():
                if schwab_field in market_data:
                    value = market_data[schwab_field]
                    if value is not None:
                        try:
                            normalized[normalized_field] = float(value)
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert {schwab_field}={value} to float for {symbol}")
            
            # For symbols without LAST_PRICE, use BID_PRICE or ASK_PRICE as fallback
            if normalized["price"] is None:
                if normalized["bid"] is not None and normalized["ask"] is not None:
                    # Use mid-price as fallback
                    normalized["price"] = (normalized["bid"] + normalized["ask"]) / 2.0
                    logger.debug(f"Using mid-price {normalized['price']} for {symbol}")
                elif normalized["bid"] is not None:
                    normalized["price"] = normalized["bid"]
                    logger.debug(f"Using bid price {normalized['price']} for {symbol}")
                elif normalized["ask"] is not None:
                    normalized["price"] = normalized["ask"]
                    logger.debug(f"Using ask price {normalized['price']} for {symbol}")
            
            # Validate required fields
            if normalized["price"] is None:
                logger.warning(f"No price data available for {symbol} in {market_data}, skipping tick")
                return None
            
            # Validate price range (basic sanity check)
            if normalized["price"] <= 0 or normalized["price"] > 1000000:
                logger.warning(f"Invalid price {normalized['price']} for {symbol}")
                return None
                
            # Set default volume if not provided
            if normalized["volume"] is None:
                normalized["volume"] = 0
            
            logger.info(f"✅ Successfully normalized data for {symbol}: price={normalized['price']}, volume={normalized['volume']}, bid={normalized['bid']}, ask={normalized['ask']}")
            return normalized
            
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Failed to normalize data for {symbol}: {e}")
            return None


class DataIngestionService:
    """
    Real-time market data ingestion service.
    
    Manages Schwab API connection, data normalization, database storage,
    and real-time broadcasting with automatic error recovery and monitoring.
    """
    
    def __init__(self):
        self.schwab_client = SchwabRealTimeClient()
        self.normalizer = DataNormalizer()
        self.websocket_manager = get_websocket_manager()
        self.alert_engine = None  # Will be injected during startup
        
        # Service state
        self.is_running = False
        self.instruments_map: Dict[str, int] = {}
        
        # Performance monitoring
        self.ticks_processed = 0
        self.last_tick_time: Optional[datetime] = None
        self.processing_errors = 0
        
        # Data processing queue
        self.data_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
    
    def set_alert_engine(self, alert_engine) -> None:
        """
        Set the alert engine for real-time evaluation.
        
        Args:
            alert_engine: Alert engine instance.
        """
        self.alert_engine = alert_engine
        
    async def start(self) -> None:
        """
        Start the data ingestion service.
        
        Initializes Schwab API connection, loads instrument mapping,
        and starts background data processing.
        """
        if self.is_running:
            logger.warning("Data ingestion service already running")
            return
        
        logger.info("Starting data ingestion service")
        
        try:
            # Load instrument mapping from database
            await self._load_instruments_mapping()
            
            # Set up Schwab client callback
            self.schwab_client.set_data_callback(self._handle_market_data)
            
            # Get target symbols from database (not config)
            target_symbols = list(self.instruments_map.keys())
            
            # Start Schwab streaming
            if await self.schwab_client.start_streaming(target_symbols):
                # Start background data processing
                self.is_running = True
                asyncio.create_task(self._data_processing_loop())
                asyncio.create_task(self._connection_monitor())
                
                logger.info(f"Data ingestion service started for {len(target_symbols)} instruments: {target_symbols}")
            else:
                raise SchwabAPIError("Failed to start Schwab streaming")
                
        except Exception as e:
            logger.error(f"Failed to start data ingestion service: {e}")
            self.is_running = False
            raise
    
    async def stop(self) -> None:
        """
        Stop the data ingestion service.
        
        Gracefully shuts down Schwab API connection and data processing.
        """
        if not self.is_running:
            return
        
        logger.info("Stopping data ingestion service")
        
        self.is_running = False
        
        # Stop Schwab streaming
        await self.schwab_client.stop_streaming()
        
        # Process remaining queued data
        await self._flush_data_queue()
        
        # Close Schwab client
        await self.schwab_client.close()
        
        logger.info("Data ingestion service stopped")
    
    @with_db_session
    @handle_db_errors("Instruments mapping load")
    async def _load_instruments_mapping(self, session) -> None:
        """Load instrument symbol to ID mapping from database."""
        result = await session.execute(
            select(Instrument.id, Instrument.symbol).where(
                Instrument.status == InstrumentStatus.ACTIVE
            )
        )
        
        self.instruments_map = {
            symbol: instrument_id for instrument_id, symbol in result.all()
        }
        
        logger.info(f"Loaded {len(self.instruments_map)} instrument mappings")
    
    def _handle_market_data(self, symbol: str, raw_data: Dict[str, Any]) -> None:
        """
        Handle incoming market data from Schwab API (synchronous callback).
        
        Args:
            symbol: Instrument symbol.
            raw_data: Raw market data from API.
        """
        try:
            logger.info(f"📈 MARKET DATA CALLBACK: {symbol} - processing data")
            
            # Normalize data
            normalized_data = self.normalizer.normalize_tick_data(symbol, raw_data)
            if not normalized_data:
                return
            
            # Add to processing queue (non-blocking)
            try:
                self.data_queue.put_nowait(normalized_data)
                logger.info(f"📥 QUEUED: {symbol} - normalized data added to queue")
            except asyncio.QueueFull:
                logger.warning("Data queue full, dropping tick data")
                
        except Exception as e:
            logger.error(f"Error handling market data for {symbol}: {e}")
            self.processing_errors += 1
    
    async def _data_processing_loop(self) -> None:
        """
        Background loop for processing market data from queue.
        
        Handles batch processing of market data with database storage
        and real-time broadcasting to WebSocket clients.
        """
        batch_size = settings.DATA_INGESTION_BATCH_SIZE
        batch_timeout = 1.0  # Process batches at least every second
        
        while self.is_running:
            batch_data = []
            batch_start = asyncio.get_event_loop().time()
            
            try:
                # Collect batch data
                while (
                    len(batch_data) < batch_size and
                    (asyncio.get_event_loop().time() - batch_start) < batch_timeout
                ):
                    try:
                        data = await asyncio.wait_for(
                            self.data_queue.get(),
                            timeout=0.1
                        )
                        batch_data.append(data)
                    except asyncio.TimeoutError:
                        break
                
                # Process batch if we have data
                if batch_data:
                    await self._process_data_batch(batch_data)
                    
            except Exception as e:
                logger.error(f"Error in data processing loop: {e}")
                await asyncio.sleep(1)  # Brief pause on error
    
    @with_db_session
    @handle_db_errors("Data batch processing")
    async def _process_data_batch(self, session, batch_data: List[Dict[str, Any]]) -> None:
        """
        Process a batch of market data.
        
        Args:
            session: Database session.
            batch_data: List of normalized tick data.
        """
        logger.info(f"🔄 PROCESSING BATCH: {len(batch_data)} items")
        
        # Create MarketData records
        market_data_records = []
        
        for tick_data in batch_data:
            symbol = tick_data["symbol"]
            instrument_id = self.instruments_map.get(symbol)
            
            if not instrument_id:
                logger.warning(f"Unknown instrument symbol: {symbol}")
                continue
            
            # Create market data record
            market_data = MarketData(
                timestamp=tick_data["timestamp"],
                instrument_id=instrument_id,
                price=tick_data["price"],
                volume=tick_data["volume"],
                bid=tick_data["bid"],
                ask=tick_data["ask"],
                bid_size=tick_data["bid_size"],
                ask_size=tick_data["ask_size"],
                open_price=tick_data["open_price"],
                high_price=tick_data["high_price"],
                low_price=tick_data["low_price"],
            )
            
            market_data_records.append(market_data)
            session.add(market_data)
            
            # Update instrument last tick info
            await session.execute(
                update(Instrument)
                .where(Instrument.id == instrument_id)
                .values(
                    last_tick=tick_data["timestamp"],
                    last_price=tick_data["price"]
                )
            )
        
        # Update metrics
        self.ticks_processed += len(market_data_records)
        self.last_tick_time = datetime.utcnow()
        
        # Broadcast tick updates via WebSocket and trigger alert evaluation
        for record in market_data_records:
            logger.info(f"📡 BROADCASTING: {batch_data[market_data_records.index(record)]['symbol']} @ {record.price}")
            await self.websocket_manager.broadcast_tick_update(
            instrument_id=record.instrument_id,
                symbol=batch_data[market_data_records.index(record)]["symbol"],
                price=float(record.price) if record.price else 0.0,
                volume=record.volume or 0,
                timestamp=record.timestamp
            )
            
            # Queue alert evaluation for this market data
            if self.alert_engine:
                await self.alert_engine.queue_evaluation(record.instrument_id, record)
        
        if len(market_data_records) > 0:
            logger.info(f"✅ BATCH COMPLETE: Processed {len(market_data_records)} market data records")
    
    async def _connection_monitor(self) -> None:
        """
        Monitor connection health and trigger reconnection if needed.
        """
        check_interval = 30  # Check every 30 seconds
        
        while self.is_running:
            try:
                await asyncio.sleep(check_interval)
                
                if not self.schwab_client.is_connected:
                    logger.warning("Schwab connection lost, attempting reconnection")
                    
                    # Attempt reconnection
                    if await self.schwab_client._client.reconnect_with_backoff():
                        logger.info("Successfully reconnected to Schwab API")
                    else:
                        logger.error("Failed to reconnect to Schwab API")
                
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
    
    async def _flush_data_queue(self) -> None:
        """Process all remaining data in queue during shutdown."""
        if self.data_queue.empty():
            return
        
        logger.info("Flushing remaining data from queue")
        remaining_data = []
        
        while not self.data_queue.empty():
            try:
                data = self.data_queue.get_nowait()
                remaining_data.append(data)
            except asyncio.QueueEmpty:
                break
        
        if remaining_data:
            await self._process_data_batch(remaining_data)
            logger.info(f"Flushed {len(remaining_data)} remaining data records")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current service status and metrics.
        
        Returns:
            Dict: Service status and performance metrics.
        """
        return {
            "running": self.is_running,
            "connected": self.schwab_client.is_connected,
            "ticks_processed": self.ticks_processed,
            "last_tick_time": self.last_tick_time.isoformat() if self.last_tick_time else None,
            "processing_errors": self.processing_errors,
            "queue_size": self.data_queue.qsize(),
            "active_instruments": len(self.instruments_map),
        }