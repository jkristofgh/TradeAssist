"""
Real-time market data streaming with callback-based event handling.

Provides simplified streaming capabilities for various market data types with
automatic instrument detection and reconnection logic.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable, Set, Union
from enum import Enum

from loguru import logger
from schwab.client import Client
from schwab.streaming import StreamClient

from ..auth.manager import AuthManager, AuthenticationError
from ..utils.analyzer import SymbolAnalyzer, InstrumentProfile
from ..models import InstrumentType, StreamEvent, create_stream_event_from_message


class StreamType(str, Enum):
    """Available streaming data types."""
    LEVEL_ONE_EQUITY = "level_one_equity"
    LEVEL_ONE_OPTION = "level_one_option" 
    LEVEL_ONE_FUTURES = "level_one_futures"
    LEVEL_ONE_FOREX = "level_one_forex"
    LEVEL_ONE_INDEX = "level_one_index"
    CHART_EQUITY = "chart_equity"
    CHART_FUTURES = "chart_futures"


class StreamingError(Exception):
    """Exception for streaming operations."""
    pass


class StreamingClient:
    """
    Real-time market data streaming client with callback-based events.
    
    Provides simplified streaming interface with automatic instrument detection,
    reconnection logic, and customizable event callbacks.
    """
    
    def __init__(self, auth_manager: AuthManager) -> None:
        """
        Initialize streaming client.
        
        Args:
            auth_manager: Authentication manager for API access
        """
        self.auth_manager = auth_manager
        self.symbol_analyzer = SymbolAnalyzer()
        
        self._schwab_client: Optional[Client] = None
        self._stream_client: Optional[StreamClient] = None
        self._account_id: Optional[int] = None
        
        # Connection state
        self._is_connected = False
        self._is_running = False
        self._connection_attempts = 0
        self._last_message_time: Optional[datetime] = None
        
        # Subscription tracking
        self._active_subscriptions: Dict[StreamType, Set[str]] = {
            stream_type: set() for stream_type in StreamType
        }
        self._callbacks: List[Callable[[StreamEvent], None]] = []
        
        # Statistics
        self._message_count = 0
        self._reconnect_count = 0
        self._start_time: Optional[datetime] = None
        
        logger.info("StreamingClient initialized")
    
    def add_callback(self, callback: Callable[[StreamEvent], None]) -> None:
        """
        Add a callback function for streaming events.
        
        Args:
            callback: Function that takes a StreamEvent parameter
        """
        self._callbacks.append(callback)
        logger.debug(f"Added callback, total callbacks: {len(self._callbacks)}")
    
    def remove_callback(self, callback: Callable[[StreamEvent], None]) -> None:
        """
        Remove a callback function.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            logger.debug(f"Removed callback, remaining callbacks: {len(self._callbacks)}")
    
    def get_stream_type_for_symbol(self, symbol: str) -> StreamType:
        """
        Automatically determine the appropriate stream type for a symbol.
        
        Args:
            symbol: Trading symbol to analyze
            
        Returns:
            Appropriate StreamType for the symbol
        """
        instrument_profile = self.symbol_analyzer.analyze_symbol(symbol)
        instrument_type = instrument_profile.instrument_type
        
        # Map instrument types to stream types
        type_mapping = {
            InstrumentType.EQUITY: StreamType.LEVEL_ONE_EQUITY,
            InstrumentType.ETF: StreamType.LEVEL_ONE_EQUITY,
            InstrumentType.INDEX: StreamType.LEVEL_ONE_INDEX,
            InstrumentType.FUTURE: StreamType.LEVEL_ONE_FUTURES,
            InstrumentType.FOREX: StreamType.LEVEL_ONE_FOREX,
            InstrumentType.OPTION: StreamType.LEVEL_ONE_OPTION,
            InstrumentType.BOND: StreamType.LEVEL_ONE_EQUITY,
            InstrumentType.MUTUAL_FUND: StreamType.LEVEL_ONE_EQUITY,
        }
        
        stream_type = type_mapping.get(instrument_type, StreamType.LEVEL_ONE_EQUITY)
        
        logger.debug(f"Auto-detected {symbol} -> {instrument_type.value} -> {stream_type.value} "
                    f"(confidence: {instrument_profile.confidence:.2f})")
        
        return stream_type
    
    def group_symbols_by_stream_type(self, symbols: List[str]) -> Dict[StreamType, List[str]]:
        """
        Group symbols by their appropriate stream types.
        
        Args:
            symbols: List of symbols to group
            
        Returns:
            Dictionary mapping stream types to symbol lists
        """
        stream_groups: Dict[StreamType, List[str]] = {}
        
        for symbol in symbols:
            stream_type = self.get_stream_type_for_symbol(symbol)
            
            if stream_type not in stream_groups:
                stream_groups[stream_type] = []
            
            stream_groups[stream_type].append(symbol)
        
        # Log the grouping results
        logger.info("Symbol grouping results:")
        for stream_type, symbol_list in stream_groups.items():
            logger.info(f"  {stream_type.value}: {', '.join(symbol_list)}")
        
        return stream_groups
    
    async def stream_quotes(
        self,
        symbols: Union[str, List[str]],
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        duration: Optional[int] = None,
        auto_reconnect: bool = True
    ) -> None:
        """
        Stream real-time quotes for symbols with automatic type detection.
        
        Args:
            symbols: Symbol or list of symbols to stream
            callback: Optional simple callback function (symbol, data) 
            duration: Duration to stream in seconds (None for unlimited)
            auto_reconnect: Whether to automatically reconnect on connection loss
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        
        # Add simple callback wrapper if provided
        if callback:
            def callback_wrapper(event: StreamEvent) -> None:
                if event.event_type == 'quote':
                    callback(event.symbol, event.data)
            
            self.add_callback(callback_wrapper)
        
        try:
            await self._connect()
            
            # Group symbols by stream type
            stream_groups = self.group_symbols_by_stream_type(symbols)
            
            # Subscribe to each group
            for stream_type, symbol_list in stream_groups.items():
                await self._subscribe_symbols(stream_type, symbol_list)
            
            # Set start time and running flag
            self._start_time = datetime.now()
            self._is_running = True
            
            logger.info(f"Started streaming {len(symbols)} symbols for {duration or 'unlimited'} seconds")
            
            # Stream for specified duration or indefinitely
            if duration:
                # Stream for specific duration with handle_message() loop
                end_time = datetime.now() + timedelta(seconds=duration)
                while datetime.now() < end_time and self._is_running:
                    try:
                        await self._stream_client.handle_message()
                    except Exception as e:
                        logger.warning(f"Error handling message: {e}")
                        if auto_reconnect:
                            await self._reconnect()
                        else:
                            break
            else:
                # Stream indefinitely until stopped with handle_message() loop
                while self._is_running:
                    try:
                        await self._stream_client.handle_message()
                    except Exception as e:
                        logger.warning(f"Error handling message: {e}")
                        if auto_reconnect:
                            await self._reconnect()
                        else:
                            break
                    
                    # Check for stale connection periodically
                    if (self._last_message_time and 
                        datetime.now() - self._last_message_time > timedelta(minutes=5)):
                        logger.warning("No messages received for 5 minutes, checking connection")
                        if auto_reconnect:
                            await self._reconnect()
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise StreamingError(f"Streaming failed: {e}") from e
        
        finally:
            await self.stop()
    
    async def _connect(self) -> None:
        """Establish connection to streaming service."""
        try:
            # Get authenticated client
            self._schwab_client = self.auth_manager.get_authenticated_client()
            
            # Create stream client
            self._stream_client = StreamClient(self._schwab_client, account_id=self._get_account_id())
            
            # Login to streaming service first
            await self._stream_client.login()
            
            # Set up message handlers IMMEDIATELY after login but BEFORE subscriptions
            self._stream_client.add_level_one_equity_handler(self._handle_stream_message)
            self._stream_client.add_level_one_futures_handler(self._handle_stream_message)
            self._stream_client.add_level_one_forex_handler(self._handle_stream_message)
            self._stream_client.add_level_one_option_handler(self._handle_stream_message)
            
            self._is_connected = True
            self._connection_attempts += 1
            
            logger.info("Successfully connected to streaming service")
            
        except Exception as e:
            logger.error(f"Failed to connect to streaming service: {e}")
            raise StreamingError(f"Connection failed: {e}") from e
    
    async def _reconnect(self) -> None:
        """Reconnect to streaming service."""
        logger.info("Attempting to reconnect to streaming service")
        
        try:
            await self._disconnect()
            await asyncio.sleep(2)  # Brief pause before reconnecting
            await self._connect()
            
            # Re-subscribe to active symbols
            for stream_type, symbols in self._active_subscriptions.items():
                if symbols:
                    await self._subscribe_symbols(stream_type, list(symbols))
            
            self._reconnect_count += 1
            logger.info("Successfully reconnected to streaming service")
            
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            raise
    
    async def _disconnect(self) -> None:
        """Disconnect from streaming service."""
        try:
            if self._stream_client:
                await self._stream_client.logout()
            self._is_connected = False
            logger.debug("Disconnected from streaming service")
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")
    
    def _get_account_id(self) -> int:
        """Get account ID for streaming."""
        if self._account_id is None:
            try:
                # Get the first account from the client
                if self._schwab_client:
                    account_numbers = self._schwab_client.get_account_numbers()
                    if account_numbers:
                        # Extract the account hash from the response
                        first_account = account_numbers[0]
                        # Use hash code as account ID for streaming
                        self._account_id = hash(first_account['accountNumber']) % (10**8)
                        logger.info(f"Using account ID: {self._account_id}")
                    else:
                        self._account_id = 0  # Fallback
                else:
                    self._account_id = 0  # Fallback
            except Exception as e:
                logger.warning(f"Could not get account ID: {e}, using fallback")
                self._account_id = 0
        return self._account_id
    
    async def _subscribe_symbols(self, stream_type: StreamType, symbols: List[str]) -> None:
        """Subscribe to symbols for a specific stream type."""
        if not self._stream_client:
            raise StreamingError("Not connected to streaming service")
        
        try:
            logger.info(f"Subscribing to {len(symbols)} symbols for {stream_type.value}")
            
            # Map stream types to subscription methods
            if stream_type == StreamType.LEVEL_ONE_EQUITY:
                await self._stream_client.level_one_equity_subs(symbols)
            elif stream_type == StreamType.LEVEL_ONE_FUTURES:
                await self._stream_client.level_one_futures_subs(symbols)
            elif stream_type == StreamType.LEVEL_ONE_OPTION:
                await self._stream_client.level_one_option_subs(symbols)
            elif stream_type == StreamType.LEVEL_ONE_FOREX:
                await self._stream_client.level_one_forex_subs(symbols)
            elif stream_type == StreamType.LEVEL_ONE_INDEX:
                # For indices, try equity subscription first
                await self._stream_client.level_one_equity_subs(symbols)
            else:
                logger.warning(f"Unsupported stream type: {stream_type}")
                return
            
            # Track active subscriptions
            self._active_subscriptions[stream_type].update(symbols)
            
            logger.info(f"Successfully subscribed to {stream_type.value} for: {', '.join(symbols)}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {stream_type.value}: {e}")
            raise StreamingError(f"Subscription failed: {e}") from e
    
    def _handle_stream_message(self, message: Dict[str, Any]) -> None:
        """
        Handle incoming streaming messages and dispatch to callbacks.
        
        Args:
            message: Raw streaming message from schwab-py
        """
        try:
            self._last_message_time = datetime.now()
            self._message_count += 1
            
            # Debug: Log raw message structure
            logger.debug(f"Raw streaming message received: {message}")
            
            # Extract symbol and event type from message
            symbol = self._extract_symbol_from_message(message)
            event_type = self._extract_event_type_from_message(message)
            
            logger.debug(f"Extracted - Symbol: {symbol}, Event Type: {event_type}")
            
            if symbol and event_type:
                # Create StreamEvent
                stream_event = create_stream_event_from_message(
                    symbol=symbol,
                    message_data=message,
                    event_type=event_type
                )
                
                logger.info(f"Dispatching stream event: {symbol} - {event_type}")
                
                # Dispatch to all callbacks
                for callback in self._callbacks:
                    try:
                        callback(stream_event)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
            else:
                logger.warning(f"Could not extract symbol/event from message: {message}")
            
        except Exception as e:
            logger.error(f"Error handling stream message: {e}")
    
    def _extract_symbol_from_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Extract symbol from streaming message."""
        # Handle schwab-py message format with 'content' array
        if 'content' in message:
            content_list = message['content']
            if content_list and len(content_list) > 0:
                # Return the first symbol from the content array
                return content_list[0].get('key')
        
        # Handle legacy format with 'data' array
        if 'data' in message:
            data_list = message['data']
            if data_list and len(data_list) > 0:
                content = data_list[0].get('content', [])
                if content and len(content) > 0:
                    return content[0].get('key')
        
        # Fallback for other message types
        return message.get('key', message.get('symbol'))
    
    def _extract_event_type_from_message(self, message: Dict[str, Any]) -> str:
        """Extract event type from streaming message."""
        # Handle schwab-py message format
        if 'data' in message:
            data_list = message['data']
            if data_list and len(data_list) > 0:
                service = data_list[0].get('service', '')
                if 'LEVELONE' in service:
                    return 'quote'
                elif 'CHART' in service:
                    return 'chart'
        
        # Fallback
        service = message.get('service', '')
        if 'LEVELONE' in service:
            return 'quote'
        elif 'CHART' in service:
            return 'chart'
        else:
            return 'unknown'
    
    async def stop(self) -> None:
        """Stop streaming and cleanup resources."""
        logger.info("Stopping streaming client")
        
        self._is_running = False
        
        try:
            await self._disconnect()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
        
        # Clear subscriptions and callbacks
        for stream_type in self._active_subscriptions:
            self._active_subscriptions[stream_type].clear()
        
        self._callbacks.clear()
        
        # Log session statistics
        if self._start_time:
            duration = datetime.now() - self._start_time
            logger.info(f"Streaming session ended. Duration: {duration}, Messages: {self._message_count}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get streaming session statistics."""
        stats = {
            "is_connected": self._is_connected,
            "is_running": self._is_running,
            "message_count": self._message_count,
            "connection_attempts": self._connection_attempts,
            "reconnect_count": self._reconnect_count,
            "active_callbacks": len(self._callbacks),
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "last_message_time": self._last_message_time.isoformat() if self._last_message_time else None,
            "active_subscriptions": {
                str(stream_type): list(symbols) 
                for stream_type, symbols in self._active_subscriptions.items()
                if symbols
            }
        }
        
        if self._start_time:
            stats["session_duration_seconds"] = int((datetime.now() - self._start_time).total_seconds())
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check of the streaming client."""
        health: Dict[str, Any] = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Check connection status
            if self._is_running and not self._is_connected:
                health["status"] = "unhealthy"
                health["issues"].append("Should be running but not connected")
                health["recommendations"].append("Check network connectivity and authentication")
            
            # Check for stale data
            if (self._last_message_time and 
                datetime.now() - self._last_message_time > timedelta(minutes=5)):
                health["status"] = "degraded"
                health["issues"].append("No messages received in last 5 minutes")
                health["recommendations"].append("Consider reconnecting")
            
            # Check authentication
            auth_health = self.auth_manager.health_check()
            if auth_health["status"] != "healthy":
                health["status"] = "degraded"
                health["issues"].extend(auth_health["issues"])
                health["recommendations"].extend(auth_health["recommendations"])
                
        except Exception as e:
            health["status"] = "error"
            health["issues"].append(f"Health check failed: {e}")
        
        return health


# Convenience function for simple streaming
async def stream_quotes(
    symbols: Union[str, List[str]],
    callback: Callable[[str, Dict[str, Any]], None],
    api_key: str,
    app_secret: str,
    duration: Optional[int] = None,
    callback_url: str = "https://localhost:8080/callback"
) -> None:
    """
    Convenience function to stream quotes with minimal setup.
    
    Args:
        symbols: Symbol or list of symbols to stream
        callback: Callback function (symbol, data)
        api_key: Schwab API key
        app_secret: Schwab app secret
        duration: Duration to stream in seconds
        callback_url: OAuth callback URL
    """
    from ..auth.manager import AuthManager
    
    auth_manager = AuthManager(api_key, app_secret, callback_url)
    client = StreamingClient(auth_manager)
    
    await client.stream_quotes(symbols, callback, duration)


# Export key classes and functions
__all__ = [
    "StreamingClient",
    "StreamType",
    "StreamingError", 
    "stream_quotes"
]