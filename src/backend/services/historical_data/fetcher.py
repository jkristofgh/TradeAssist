"""
Historical Data Fetcher Component

Handles all data retrieval operations from external APIs.
Extracted from HistoricalDataService as part of Phase 3 decomposition.
"""

import asyncio
import random
import structlog
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable

from ...config import settings
from ...models.historical_data import DataFrequency
from ...integrations.schwab_client import TradeAssistSchwabClient

logger = structlog.get_logger()


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open due to API failures."""
    pass


class RateLimitError(Exception):
    """Raised when rate limits are exceeded."""
    pass


class HistoricalDataFetcher:
    """
    Handles all data retrieval operations from external APIs.
    
    Responsibilities:
    - Schwab API integration with authentication
    - Rate limiting and circuit breaker implementation  
    - Mock data generation for development/testing
    - Response transformation and normalization
    - Error handling for external API failures
    - Progress tracking for multiple symbol requests
    """
    
    def __init__(self, schwab_client: Optional[TradeAssistSchwabClient] = None):
        self.schwab_client = schwab_client
        self._last_api_call: Optional[datetime] = None
        self._min_api_interval = 0.5  # Rate limiting in seconds
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 5
        self._mock_data_enabled = None  # Lazy initialization
        
        # Performance tracking
        self._api_calls_made = 0
        self._mock_data_calls = 0
        self._circuit_breaker_trips = 0
        
        logger.debug("HistoricalDataFetcher initialized")

    async def fetch_symbol_data(
        self, 
        symbol: str, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        frequency: str = DataFrequency.DAILY.value,
        include_extended_hours: bool = False,
        max_records: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Primary data fetching method for a single symbol.
        
        Args:
            symbol: Trading symbol (e.g., "AAPL")
            start_date: Start date for data retrieval
            end_date: End date for data retrieval  
            frequency: Data frequency (from DataFrequency enum)
            include_extended_hours: Whether to include extended hours data
            max_records: Maximum number of records to return
            
        Returns:
            List of market data bars as dictionaries
            
        Raises:
            CircuitBreakerError: When external API is failing
            RateLimitError: When rate limits are exceeded
            ValueError: When parameters are invalid
        """
        logger.debug(
            f"Fetching data for {symbol}",
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            include_extended_hours=include_extended_hours
        )
        
        # Validate parameters
        if not symbol:
            raise ValueError("Symbol cannot be empty")
            
        # Enforce rate limiting
        await self._enforce_rate_limiting()
        
        # Check circuit breaker
        if self._circuit_breaker_failures >= self._circuit_breaker_threshold:
            self._circuit_breaker_trips += 1
            raise CircuitBreakerError(
                f"Circuit breaker is open after {self._circuit_breaker_failures} failures"
            )
            
        try:
            if self._should_use_mock_data():
                logger.debug(f"Using mock data for {symbol}")
                bars = await self.generate_mock_data(symbol, start_date, end_date, frequency)
                self._mock_data_calls += 1
            else:
                logger.debug(f"Using Schwab API for {symbol}")
                bars = await self._fetch_from_schwab_api(
                    symbol, start_date, end_date, frequency, include_extended_hours
                )
                
            # Reset circuit breaker on success
            self._circuit_breaker_failures = 0
            self._last_api_call = datetime.utcnow()
            self._api_calls_made += 1
            
            # Apply max_records limit if specified
            if max_records and len(bars) > max_records:
                bars = bars[:max_records]
                logger.debug(f"Limited results to {max_records} bars for {symbol}")
                
            logger.info(f"Successfully fetched {len(bars)} bars for {symbol}")
            return bars
            
        except Exception as e:
            self._circuit_breaker_failures += 1
            logger.error(
                f"Failed to fetch data for {symbol}",
                error=str(e),
                failures=self._circuit_breaker_failures
            )
            
            # If we haven't hit the circuit breaker threshold and it's not a critical error,
            # try fallback to mock data in development
            if (self._circuit_breaker_failures < self._circuit_breaker_threshold and 
                settings.DEMO_MODE):
                logger.warning(f"Falling back to mock data for {symbol}")
                return await self.generate_mock_data(symbol, start_date, end_date, frequency)
                
            raise

    async def fetch_multiple_symbols(
        self, 
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        frequency: str = DataFrequency.DAILY.value,
        include_extended_hours: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch data for multiple symbols with progress tracking.
        
        Args:
            symbols: List of trading symbols
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            frequency: Data frequency
            include_extended_hours: Whether to include extended hours data
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary mapping symbols to their market data bars
            
        Raises:
            ValueError: If no symbols provided
        """
        if not symbols:
            raise ValueError("At least one symbol is required")
            
        logger.info(f"Fetching data for {len(symbols)} symbols")
        
        results = {}
        total_symbols = len(symbols)
        
        for idx, symbol in enumerate(symbols):
            try:
                logger.debug(f"Processing symbol {idx + 1}/{total_symbols}: {symbol}")
                
                data = await self.fetch_symbol_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency,
                    include_extended_hours=include_extended_hours
                )
                results[symbol] = data
                
                # Report progress
                if progress_callback:
                    progress = (idx + 1) / total_symbols * 100
                    try:
                        if asyncio.iscoroutinefunction(progress_callback):
                            await progress_callback(f"Fetched {symbol}", progress)
                        else:
                            progress_callback(f"Fetched {symbol}", progress)
                    except Exception as e:
                        logger.warning(f"Progress callback failed: {e}")
                        
            except Exception as e:
                logger.error(f"Failed to fetch data for {symbol}: {e}")
                # Store empty list for failed symbols to maintain consistency
                results[symbol] = []
                
        logger.info(
            f"Multi-symbol fetch completed: {len([r for r in results.values() if r])} "
            f"successful out of {total_symbols} symbols"
        )
        return results

    async def generate_mock_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        frequency: str = DataFrequency.DAILY.value
    ) -> List[Dict[str, Any]]:
        """
        Generate realistic mock market data for development and testing.
        
        Args:
            symbol: Trading symbol
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to now)
            frequency: Data frequency (currently supports daily)
            
        Returns:
            List of mock market data bars
        """
        # Set default date range
        end_date = end_date or datetime.utcnow()
        start_date = start_date or (end_date - timedelta(days=30))
        
        logger.debug(
            f"Generating mock data for {symbol}",
            start_date=start_date,
            end_date=end_date,
            frequency=frequency
        )
        
        bars = []
        current_date = start_date
        base_price = self._get_base_price_for_symbol(symbol)
        
        # Calculate time delta based on frequency
        time_delta = self._get_time_delta_for_frequency(frequency)
        
        while current_date <= end_date:
            # Generate realistic OHLC data with some volatility
            volatility = 0.02  # 2% volatility
            
            # Price walk based on previous close
            price_change = random.uniform(-volatility, volatility)
            open_price = base_price * (1 + price_change)
            
            # Intraday movement
            intraday_volatility = 0.01  # 1% intraday volatility
            close_change = random.uniform(-intraday_volatility, intraday_volatility)
            close_price = open_price * (1 + close_change)
            
            # High and low with realistic ranges
            high_range = random.uniform(0, 0.015)  # Up to 1.5% above
            low_range = random.uniform(0, 0.015)   # Up to 1.5% below
            
            high_price = max(open_price, close_price) * (1 + high_range)
            low_price = min(open_price, close_price) * (1 - low_range)
            
            # Generate realistic volume
            base_volume = 1000000  # 1M shares base
            volume_variance = random.uniform(0.5, 2.0)  # 50% to 200% of base
            volume = int(base_volume * volume_variance)
            
            bar = {
                "timestamp": current_date,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume
            }
            bars.append(bar)
            
            # Update base price for next iteration (price continuity)
            base_price = close_price
            current_date += time_delta
            
        logger.debug(f"Generated {len(bars)} mock bars for {symbol}")
        return bars

    async def get_fetcher_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the fetcher component.
        
        Returns:
            Dictionary with fetcher performance metrics
        """
        return {
            "api_calls_made": self._api_calls_made,
            "mock_data_calls": self._mock_data_calls,
            "circuit_breaker_failures": self._circuit_breaker_failures,
            "circuit_breaker_trips": self._circuit_breaker_trips,
            "circuit_breaker_open": (
                self._circuit_breaker_failures >= self._circuit_breaker_threshold
            ),
            "last_api_call": self._last_api_call,
            "schwab_client_connected": (
                self.schwab_client and hasattr(self.schwab_client, 'is_connected') and
                self.schwab_client.is_connected
            ),
            "mock_mode": self._should_use_mock_data()
        }

    # Private helper methods
    
    async def _enforce_rate_limiting(self) -> None:
        """Ensure API rate limits are respected."""
        if self._last_api_call:
            elapsed = (datetime.utcnow() - self._last_api_call).total_seconds()
            if elapsed < self._min_api_interval:
                sleep_time = self._min_api_interval - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)

    def _should_use_mock_data(self) -> bool:
        """Determine if mock data should be used based on environment settings."""
        if self._mock_data_enabled is None:
            self._mock_data_enabled = (
                settings.DEMO_MODE or 
                not self.schwab_client or
                getattr(settings, 'USE_MOCK_DATA', False)
            )
        return self._mock_data_enabled

    async def _fetch_from_schwab_api(
        self,
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime], 
        frequency: str,
        include_extended_hours: bool
    ) -> List[Dict[str, Any]]:
        """Fetch data from Schwab API with proper error handling."""
        if not self.schwab_client:
            raise RuntimeError("Schwab client not available")
            
        # Map frequency to schwab_package format
        frequency_map = {
            DataFrequency.ONE_MINUTE.value: "1m",
            DataFrequency.FIVE_MINUTE.value: "5m",
            DataFrequency.FIFTEEN_MINUTE.value: "15m",
            DataFrequency.THIRTY_MINUTE.value: "30m",
            DataFrequency.ONE_HOUR.value: "1h",
            DataFrequency.FOUR_HOUR.value: "4h",
            DataFrequency.DAILY.value: "daily",
            DataFrequency.WEEKLY.value: "weekly",
            DataFrequency.MONTHLY.value: "monthly"
        }
        
        schwab_frequency = frequency_map.get(frequency, "daily")
        days_back = None
        
        # If no dates provided, default to last 30 days
        if not start_date and not end_date:
            days_back = 30
            
        logger.debug(
            f"Calling Schwab API for {symbol}",
            schwab_frequency=schwab_frequency,
            start_date=start_date,
            end_date=end_date,
            days_back=days_back
        )
        
        # Call the schwab client's get_historical_data method
        df = await self.schwab_client.client.get_historical_data(
            symbol=symbol,
            interval=schwab_frequency,
            start_date=start_date,
            end_date=end_date,
            days_back=days_back,
            include_extended_hours=include_extended_hours
        )
        
        return self._transform_schwab_response(df, symbol)

    def _transform_schwab_response(self, df, symbol: str) -> List[Dict[str, Any]]:
        """Transform Schwab API response to internal MarketDataBar format."""
        if df is None or df.empty:
            logger.warning(f"No data returned from Schwab API for {symbol}")
            return []
            
        bars = []
        for idx, row in df.iterrows():
            try:
                bar = {
                    "timestamp": (
                        idx if isinstance(idx, datetime) 
                        else datetime.fromisoformat(str(idx))
                    ),
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)), 
                    "close": float(row.get("close", 0)),
                    "volume": int(row.get("volume", 0))
                }
                bars.append(bar)
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid row data for {symbol}: {e}")
                continue
                
        logger.info(f"Transformed {len(bars)} bars for {symbol} from Schwab API")
        return bars

    def _get_base_price_for_symbol(self, symbol: str) -> float:
        """Get a realistic base price for a symbol for mock data generation."""
        # Simple heuristic based on symbol characteristics
        base_prices = {
            "AAPL": 150.0,
            "GOOGL": 2500.0,
            "MSFT": 300.0,
            "TSLA": 200.0,
            "AMZN": 3000.0,
            "NVDA": 400.0,
            "META": 250.0,
            "BRK.A": 400000.0,
            "SPY": 400.0,
            "QQQ": 350.0,
        }
        
        # If known symbol, use predefined price
        if symbol in base_prices:
            return base_prices[symbol]
            
        # Otherwise, generate a reasonable price based on symbol characteristics
        if len(symbol) <= 2:
            # Likely ETF or major stock
            return random.uniform(50, 500)
        elif symbol.endswith('.A') or symbol.endswith('.B'):
            # Class A/B shares, potentially higher priced
            return random.uniform(100, 1000)
        else:
            # Regular stock
            return random.uniform(10, 200)

    def _get_time_delta_for_frequency(self, frequency: str) -> timedelta:
        """Get time delta for frequency progression in mock data."""
        frequency_deltas = {
            DataFrequency.ONE_MINUTE.value: timedelta(minutes=1),
            DataFrequency.FIVE_MINUTE.value: timedelta(minutes=5),
            DataFrequency.FIFTEEN_MINUTE.value: timedelta(minutes=15),
            DataFrequency.THIRTY_MINUTE.value: timedelta(minutes=30),
            DataFrequency.ONE_HOUR.value: timedelta(hours=1),
            DataFrequency.FOUR_HOUR.value: timedelta(hours=4),
            DataFrequency.DAILY.value: timedelta(days=1),
            DataFrequency.WEEKLY.value: timedelta(weeks=1),
            DataFrequency.MONTHLY.value: timedelta(days=30),  # Approximate
        }
        
        return frequency_deltas.get(frequency, timedelta(days=1))