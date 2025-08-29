"""
Historical data retrieval for Schwab market data.

Provides simplified historical data retrieval with pandas DataFrame output,
intelligent symbol analysis, and automatic rate limiting.
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, Union
from enum import Enum

import pandas as pd
from loguru import logger

from ..auth.manager import AuthManager, AuthenticationError
from ..utils.rate_limiter import APIRequestTracker, RateLimitError
from ..utils.analyzer import SymbolAnalyzer, InstrumentProfile
from ..models import InstrumentType


class HistoricalInterval(str, Enum):
    """Supported historical data intervals."""
    MINUTE = "1m"
    FIVE_MINUTES = "5m"
    TEN_MINUTES = "10m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    DAILY = "1d"
    WEEKLY = "1w"


class HistoricalDataError(Exception):
    """Exception for historical data operations."""
    pass


class HistoricalDataRetriever:
    """
    Simplified historical data retrieval with DataFrame output.
    
    Provides a clean interface for getting historical market data with automatic
    symbol analysis, rate limiting, and pandas DataFrame return format.
    """
    
    # Mapping of intervals to schwab-py methods
    INTERVAL_METHODS = {
        HistoricalInterval.MINUTE: "get_price_history_every_minute",
        HistoricalInterval.FIVE_MINUTES: "get_price_history_every_five_minutes",
        HistoricalInterval.TEN_MINUTES: "get_price_history_every_ten_minutes",
        HistoricalInterval.FIFTEEN_MINUTES: "get_price_history_every_fifteen_minutes",
        HistoricalInterval.THIRTY_MINUTES: "get_price_history_every_thirty_minutes",
        HistoricalInterval.DAILY: "get_price_history_every_day",
        HistoricalInterval.WEEKLY: "get_price_history_every_week",
    }
    
    # Maximum lookback periods for each interval (conservative estimates)
    INTERVAL_LIMITS = {
        HistoricalInterval.MINUTE: timedelta(days=48),
        HistoricalInterval.FIVE_MINUTES: timedelta(days=270),  # ~9 months
        HistoricalInterval.TEN_MINUTES: timedelta(days=270),
        HistoricalInterval.FIFTEEN_MINUTES: timedelta(days=270),
        HistoricalInterval.THIRTY_MINUTES: timedelta(days=270),
        HistoricalInterval.DAILY: timedelta(days=365 * 20),  # 20 years
        HistoricalInterval.WEEKLY: timedelta(days=365 * 20),
    }
    
    def __init__(self, auth_manager: AuthManager):
        """
        Initialize historical data retriever.
        
        Args:
            auth_manager: Authentication manager for API access
        """
        self.auth_manager = auth_manager
        self.request_tracker = APIRequestTracker()
        self.symbol_analyzer = SymbolAnalyzer()
        
        logger.info("HistoricalDataRetriever initialized")
    
    async def get_historical_data(
        self,
        symbol: str,
        interval: Union[str, HistoricalInterval] = HistoricalInterval.DAILY,
        start_date: Optional[Union[datetime, date, str]] = None,
        end_date: Optional[Union[datetime, date, str]] = None,
        days_back: Optional[int] = None,
        include_extended_hours: bool = False,
        include_previous_close: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve historical data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "AAPL", "/ES", "SPX")
            interval: Data interval (daily, minute, etc.)
            start_date: Start date (optional, can be datetime, date, or string)
            end_date: End date (optional, defaults to today)
            days_back: Alternative to start_date - number of days back from end_date
            include_extended_hours: Include extended hours data
            include_previous_close: Include previous close in response
            
        Returns:
            DataFrame with columns: open, high, low, close, volume, datetime
            Returns None if request fails
            
        Raises:
            HistoricalDataError: If request fails or parameters are invalid
        """
        try:
            # Normalize interval
            if isinstance(interval, str):
                try:
                    interval = HistoricalInterval(interval)
                except ValueError:
                    raise HistoricalDataError(f"Invalid interval: {interval}")
            
            # Analyze symbol for instrument-specific handling
            instrument_profile = self.symbol_analyzer.analyze_symbol(symbol)
            logger.info(f"Detected {symbol} as {instrument_profile.instrument_type.value} "
                       f"(confidence: {instrument_profile.confidence:.2f})")
            
            # Check extended hours support
            if include_extended_hours and not instrument_profile.extended_hours_supported:
                logger.warning(f"Extended hours not supported for {instrument_profile.instrument_type.value}, "
                              f"ignoring extended hours request")
                include_extended_hours = False
            
            # Normalize and validate dates
            start_datetime, end_datetime = self._normalize_dates(
                start_date, end_date, days_back, interval, instrument_profile
            )
            
            # Validate date range
            self._validate_date_range(start_datetime, end_datetime, interval, instrument_profile)
            
            logger.info(f"Getting {interval.value} data for {symbol} "
                       f"from {start_datetime.date()} to {end_datetime.date()}")
            
            # Get authenticated client
            client = self.auth_manager.get_authenticated_client()
            
            # Determine API method to use
            method_name = self._get_api_method(interval, instrument_profile)
            
            # Make the API request with rate limiting
            async def api_request() -> Any:
                method = getattr(client, method_name)
                return method(
                    symbol,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    need_extended_hours_data=include_extended_hours,
                    need_previous_close=include_previous_close
                )
            
            response = await self.request_tracker.make_request(api_request)
            
            if not response or response.status_code != 200:
                error_msg = f"API request failed: {response.status_code if response else 'No response'}"
                logger.error(error_msg)
                raise HistoricalDataError(error_msg)
            
            # Parse response to DataFrame
            df = self._parse_response_to_dataframe(response.json(), symbol, interval)
            
            if df is not None and not df.empty:
                logger.info(f"Retrieved {len(df)} {interval.value} records for {symbol}")
                return df
            else:
                logger.warning(f"No historical data returned for {symbol}")
                return None
                
        except AuthenticationError as e:
            error_msg = f"Authentication failed for {symbol}: {e}"
            logger.error(error_msg)
            raise HistoricalDataError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Failed to retrieve historical data for {symbol}: {e}"
            logger.error(error_msg)
            raise HistoricalDataError(error_msg) from e
    
    def _normalize_dates(
        self,
        start_date: Optional[Union[datetime, date, str]],
        end_date: Optional[Union[datetime, date, str]],
        days_back: Optional[int],
        interval: HistoricalInterval,
        instrument_profile: InstrumentProfile
    ) -> tuple[datetime, datetime]:
        """Normalize and validate date inputs."""
        
        # Set end date
        if end_date is None:
            end_datetime = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
        else:
            end_datetime = self._parse_date(end_date)
            if end_datetime.time() == datetime.min.time():  # Date only, no time
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
        
        # Set start date
        if start_date is not None:
            start_datetime = self._parse_date(start_date)
            if start_datetime.time() == datetime.min.time():  # Date only, no time
                start_datetime = start_datetime.replace(hour=0, minute=0, second=0)
        elif days_back is not None:
            start_datetime = end_datetime - timedelta(days=days_back)
        else:
            # Use default based on instrument type and interval
            default_days = self._get_default_lookback_days(interval, instrument_profile)
            start_datetime = end_datetime - timedelta(days=default_days)
        
        return start_datetime, end_datetime
    
    def _parse_date(self, date_input: Union[datetime, date, str]) -> datetime:
        """Parse various date input formats."""
        if isinstance(date_input, datetime):
            return date_input
        elif isinstance(date_input, date):
            return datetime.combine(date_input, datetime.min.time())
        elif isinstance(date_input, str):
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(date_input, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date string: {date_input}")
        else:
            raise ValueError(f"Invalid date type: {type(date_input)}")
    
    def _get_default_lookback_days(
        self, 
        interval: HistoricalInterval, 
        instrument_profile: InstrumentProfile
    ) -> int:
        """Get default lookback period for interval and instrument type."""
        
        # Use instrument-specific defaults if available
        if hasattr(instrument_profile, 'default_interval_days'):
            base_days = instrument_profile.default_interval_days
        else:
            base_days = 365  # Default fallback
        
        # Adjust based on interval
        if interval in [HistoricalInterval.MINUTE, HistoricalInterval.FIVE_MINUTES]:
            return min(30, base_days)  # Shorter for minute data
        elif interval in [HistoricalInterval.TEN_MINUTES, HistoricalInterval.FIFTEEN_MINUTES, 
                         HistoricalInterval.THIRTY_MINUTES]:
            return min(90, base_days)  # Medium for intraday
        else:
            return min(365, base_days)  # Longer for daily/weekly
    
    def _validate_date_range(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        interval: HistoricalInterval,
        instrument_profile: InstrumentProfile
    ) -> None:
        """Validate date range against API limits."""
        
        # Check basic date logic
        if start_datetime >= end_datetime:
            raise HistoricalDataError("Start date must be before end date")
        
        # Check against interval limits
        max_lookback = self.INTERVAL_LIMITS.get(interval, timedelta(days=365))
        if end_datetime - start_datetime > max_lookback:
            raise HistoricalDataError(
                f"Date range too large for {interval.value}. "
                f"Maximum lookback: {max_lookback.days} days"
            )
        
        # Check against instrument-specific limits
        if hasattr(instrument_profile, 'max_daily_lookback'):
            max_days = instrument_profile.max_daily_lookback
            if interval == HistoricalInterval.DAILY and end_datetime - start_datetime > max_days:
                raise HistoricalDataError(
                    f"Date range too large for {instrument_profile.instrument_type.value}. "
                    f"Maximum: {max_days.days} days"
                )
    
    def _get_api_method(
        self, 
        interval: HistoricalInterval, 
        instrument_profile: InstrumentProfile
    ) -> str:
        """Get appropriate API method for interval and instrument type."""
        
        # Check for instrument-specific override
        if instrument_profile.api_method_override:
            return instrument_profile.api_method_override
        
        # Use standard interval mapping
        return self.INTERVAL_METHODS.get(interval, "get_price_history_every_day")
    
    def _parse_response_to_dataframe(
        self, 
        response_data: Dict[str, Any], 
        symbol: str, 
        interval: HistoricalInterval
    ) -> Optional[pd.DataFrame]:
        """
        Parse Schwab API response to pandas DataFrame.
        
        Args:
            response_data: Raw API response data
            symbol: Trading symbol
            interval: Data interval
            
        Returns:
            DataFrame with OHLCV data or None if parsing fails
        """
        try:
            # Extract candles from response
            candles = response_data.get('candles', [])
            if not candles:
                logger.warning(f"No candles found in response for {symbol}")
                return None
            
            # Convert to DataFrame
            df_data = []
            for candle in candles:
                # Handle timestamp conversion
                timestamp = candle.get('datetime')
                if timestamp:
                    # Convert milliseconds to datetime
                    dt = datetime.fromtimestamp(timestamp / 1000)
                else:
                    continue
                
                df_data.append({
                    'datetime': dt,
                    'open': float(candle.get('open', 0)),
                    'high': float(candle.get('high', 0)),
                    'low': float(candle.get('low', 0)),
                    'close': float(candle.get('close', 0)),
                    'volume': int(candle.get('volume', 0))
                })
            
            if not df_data:
                logger.warning(f"No valid candle data found for {symbol}")
                return None
            
            # Create DataFrame
            df = pd.DataFrame(df_data)
            
            # Set datetime as index
            df.set_index('datetime', inplace=True)
            
            # Sort by datetime
            df.sort_index(inplace=True)
            
            # Add metadata as attributes
            df.attrs = {
                'symbol': symbol,
                'interval': interval.value,
                'source': 'schwab_package',
                'retrieved_at': datetime.now().isoformat()
            }
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to parse response to DataFrame for {symbol}: {e}")
            return None
    
    def get_request_statistics(self) -> Dict[str, Any]:
        """Get request tracking statistics."""
        return self.request_tracker.get_statistics()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check of the historical data retriever."""
        health: Dict[str, Any] = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Check authentication
            auth_health = self.auth_manager.health_check()
            if auth_health["status"] != "healthy":
                health["issues"].extend(auth_health["issues"])
                health["recommendations"].extend(auth_health["recommendations"])
            
            # Check request tracker
            tracker_health = self.request_tracker.health_check()
            if tracker_health["status"] != "healthy":
                health["issues"].extend(tracker_health["issues"])
                health["recommendations"].extend(tracker_health["recommendations"])
            
            # Overall status
            if health["issues"]:
                health["status"] = "degraded" if len(health["issues"]) <= 2 else "unhealthy"
                
        except Exception as e:
            health["status"] = "error"
            health["issues"].append(f"Health check failed: {e}")
        
        return health


# Convenience function for simple use cases
async def get_historical_data(
    symbol: str,
    api_key: str,
    app_secret: str,
    callback_url: str = "https://localhost:8080/callback",
    **kwargs: Any
) -> Optional[pd.DataFrame]:
    """
    Convenience function to get historical data with minimal setup.
    
    Args:
        symbol: Trading symbol
        api_key: Schwab API key
        app_secret: Schwab app secret
        callback_url: OAuth callback URL
        **kwargs: Additional arguments for get_historical_data
        
    Returns:
        DataFrame with historical data or None if failed
    """
    from ..auth.manager import AuthManager
    
    auth_manager = AuthManager(api_key, app_secret, callback_url)
    retriever = HistoricalDataRetriever(auth_manager)
    
    return await retriever.get_historical_data(symbol, **kwargs)


# Export key classes and functions
__all__ = [
    "HistoricalDataRetriever",
    "HistoricalInterval", 
    "HistoricalDataError",
    "get_historical_data"
]