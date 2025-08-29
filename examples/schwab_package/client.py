"""
Main Schwab client providing simplified access to market data.

This is the primary interface for the schwab-package, providing a clean facade
over the complex underlying functionality for historical and streaming data.
"""

from collections.abc import Callable
from datetime import date, datetime
from typing import Any

import pandas as pd
from loguru import logger

from .auth.manager import AuthenticationError, AuthManager
from .data.historical import HistoricalDataError, HistoricalDataRetriever, HistoricalInterval
from .data.streaming import StreamingClient, StreamingError
from .models import StreamEvent
from .utils.analyzer import SymbolAnalyzer


class SchwabClientError(Exception):
    """Base exception for SchwabClient operations."""

    pass


class SchwabClient:
    """
    Simple, powerful interface to Schwab market data.

    Provides a clean facade over historical data retrieval and real-time streaming
    with automatic authentication, rate limiting, and symbol analysis.

    Example:
        ```python
        from schwab_package import SchwabClient

        # Initialize client
        client = SchwabClient(
            api_key="your_api_key",
            app_secret="your_app_secret",
            callback_url="https://localhost:8080/callback"
        )

        # Get historical data
        df = await client.get_historical_data("AAPL", interval="daily", days_back=30)

        # Stream real-time data
        def on_quote(symbol, quote_data):
            print(f"{symbol}: ${quote_data['last']}")

        await client.stream_quotes(["AAPL", "/ES"], callback=on_quote, duration=60)
        ```
    """

    def __init__(
        self,
        api_key: str,
        app_secret: str,
        callback_url: str = "https://localhost:8080/callback",
        token_file: str = "schwab_tokens.json",
        use_gcp: bool = False,
        gcp_project_id: str | None = None,
    ):
        """
        Initialize Schwab client.

        Args:
            api_key: Schwab API key
            app_secret: Schwab app secret
            callback_url: OAuth callback URL (default: localhost)
            token_file: Path to token file for storage (default: schwab_tokens.json)
            use_gcp: Whether to use GCP for token storage (requires google-cloud packages)
            gcp_project_id: GCP project ID (required if use_gcp=True)

        Raises:
            SchwabClientError: If initialization fails
        """
        try:
            # Initialize authentication manager
            self._auth_manager = AuthManager(
                api_key=api_key,
                app_secret=app_secret,
                callback_url=callback_url,
                token_file=token_file,
                use_gcp=use_gcp,
                gcp_project_id=gcp_project_id,
            )

            # Initialize data retrieval components
            self._historical_retriever = HistoricalDataRetriever(self._auth_manager)
            self._streaming_client = StreamingClient(self._auth_manager)

            # Initialize symbol analyzer for public access
            self.symbol_analyzer = SymbolAnalyzer()

            logger.info("SchwabClient initialized successfully")

        except Exception as e:
            error_msg = f"Failed to initialize SchwabClient: {e}"
            logger.error(error_msg)
            raise SchwabClientError(error_msg) from e

    async def get_historical_data(
        self,
        symbol: str,
        interval: str | HistoricalInterval = "daily",
        start_date: datetime | date | str | None = None,
        end_date: datetime | date | str | None = None,
        days_back: int | None = None,
        include_extended_hours: bool = False,
    ) -> pd.DataFrame | None:
        """
        Get historical market data as a pandas DataFrame.

        Args:
            symbol: Trading symbol (e.g., "AAPL", "/ES", "SPX")
            interval: Data interval - "1m", "5m", "15m", "30m", "daily", "weekly"
            start_date: Start date (optional, can be datetime, date, or string)
            end_date: End date (optional, defaults to today)
            days_back: Alternative to start_date - number of days back from end_date
            include_extended_hours: Include extended hours data

        Returns:
            DataFrame with columns: open, high, low, close, volume, datetime (as index)
            Returns None if no data available

        Raises:
            SchwabClientError: If request fails

        Example:
            ```python
            # Get 30 days of daily data
            df = await client.get_historical_data("AAPL", days_back=30)

            # Get hourly data for date range
            df = await client.get_historical_data(
                "SPY",
                interval="15m",
                start_date="2024-01-01",
                end_date="2024-01-31"
            )
            ```
        """
        try:
            logger.info(f"Getting historical data for {symbol}")

            # Convert string interval to enum if needed
            if isinstance(interval, str):
                interval_map = {
                    "1m": HistoricalInterval.MINUTE,
                    "5m": HistoricalInterval.FIVE_MINUTES,
                    "10m": HistoricalInterval.TEN_MINUTES,
                    "15m": HistoricalInterval.FIFTEEN_MINUTES,
                    "30m": HistoricalInterval.THIRTY_MINUTES,
                    "daily": HistoricalInterval.DAILY,
                    "weekly": HistoricalInterval.WEEKLY,
                }
                interval = interval_map.get(interval.lower(), HistoricalInterval.DAILY)

            # Use historical data retriever
            df = await self._historical_retriever.get_historical_data(
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
                days_back=days_back,
                include_extended_hours=include_extended_hours,
            )

            if df is not None:
                logger.info(f"Retrieved {len(df)} records for {symbol}")
            else:
                logger.warning(f"No data returned for {symbol}")

            return df

        except (HistoricalDataError, AuthenticationError) as e:
            error_msg = f"Failed to get historical data for {symbol}: {e}"
            logger.error(error_msg)
            raise SchwabClientError(error_msg) from e

    async def stream_quotes(
        self,
        symbols: str | list[str],
        callback: Callable[[str, dict[str, Any]], None],
        duration: int | None = None,
        auto_reconnect: bool = True,
    ) -> None:
        """
        Stream real-time quotes with callback function.

        Args:
            symbols: Symbol or list of symbols to stream (e.g., ["AAPL", "/ES", "SPX"])
            callback: Function called for each quote update - callback(symbol, quote_data)
            duration: Duration to stream in seconds (None for unlimited)
            auto_reconnect: Whether to automatically reconnect on connection loss

        Raises:
            SchwabClientError: If streaming fails

        Example:
            ```python
            def on_quote(symbol, quote_data):
                print(f"{symbol}: ${quote_data.get('last', 'N/A')}")

            # Stream for 60 seconds
            await client.stream_quotes(["AAPL", "MSFT"], on_quote, duration=60)

            # Stream indefinitely
            await client.stream_quotes("/ES", on_quote)
            ```
        """
        try:
            if isinstance(symbols, str):
                symbols = [symbols]

            logger.info(f"Starting streaming for {len(symbols)} symbols: {', '.join(symbols)}")

            # Use streaming client
            await self._streaming_client.stream_quotes(
                symbols=symbols, callback=callback, duration=duration, auto_reconnect=auto_reconnect
            )

        except (StreamingError, AuthenticationError) as e:
            error_msg = f"Failed to stream quotes: {e}"
            logger.error(error_msg)
            raise SchwabClientError(error_msg) from e

    async def stream_quotes_advanced(
        self,
        symbols: str | list[str],
        callback: Callable[[StreamEvent], None],
        duration: int | None = None,
        auto_reconnect: bool = True,
    ) -> None:
        """
        Stream real-time quotes with advanced StreamEvent callbacks.

        This provides more detailed event information including timestamps,
        sequence IDs, and structured data.

        Args:
            symbols: Symbol or list of symbols to stream
            callback: Function called for each event - callback(stream_event)
            duration: Duration to stream in seconds (None for unlimited)
            auto_reconnect: Whether to automatically reconnect on connection loss

        Raises:
            SchwabClientError: If streaming fails

        Example:
            ```python
            def on_event(event: StreamEvent):
                quote = event.to_quote()
                if quote:
                    print(f"{quote.symbol}: ${quote.last} at {quote.timestamp}")

            await client.stream_quotes_advanced(["AAPL"], on_event)
            ```
        """
        try:
            if isinstance(symbols, str):
                symbols = [symbols]

            logger.info(f"Starting advanced streaming for {len(symbols)} symbols")

            # Add callback directly to streaming client
            self._streaming_client.add_callback(callback)

            # Start streaming without the simple callback wrapper
            await self._streaming_client.stream_quotes(
                symbols=symbols,
                callback=None,  # Use advanced callbacks only
                duration=duration,
                auto_reconnect=auto_reconnect,
            )

        except (StreamingError, AuthenticationError) as e:
            error_msg = f"Failed to stream quotes (advanced): {e}"
            logger.error(error_msg)
            raise SchwabClientError(error_msg) from e

    def authenticate_manual(self) -> None:
        """
        Perform manual OAuth authentication flow.

        This guides the user through the OAuth flow when no valid token exists.
        Call this method once to authenticate, then the client will handle
        token refresh automatically.

        Raises:
            SchwabClientError: If authentication fails
        """
        try:
            logger.info("Starting manual authentication flow")
            self._auth_manager.authenticate_manual()
            logger.info("Manual authentication completed successfully")

        except AuthenticationError as e:
            error_msg = f"Manual authentication failed: {e}"
            logger.error(error_msg)
            raise SchwabClientError(error_msg) from e

    def analyze_symbol(self, symbol: str) -> dict[str, Any]:
        """
        Analyze a symbol to determine its instrument type and characteristics.

        Args:
            symbol: Trading symbol to analyze

        Returns:
            Dictionary with symbol analysis results including:
            - instrument_type: Type of instrument (EQUITY, FUTURE, etc.)
            - confidence: Confidence score (0.0 to 1.0)
            - extended_hours_supported: Whether extended hours are supported
            - data_limits: Data availability limits

        Example:
            ```python
            info = client.analyze_symbol("AAPL")
            print(f"Type: {info['instrument_type']}")
            print(f"Confidence: {info['confidence']}")
            ```
        """
        return self.symbol_analyzer.get_symbol_info(symbol)

    def get_request_statistics(self) -> dict[str, Any]:
        """
        Get statistics about API request usage.

        Returns:
            Dictionary with request statistics including:
            - total_requests: Total number of requests made
            - success_rate: Percentage of successful requests
            - rate_limiter_stats: Current rate limiting status
        """
        historical_stats = self._historical_retriever.get_request_statistics()
        streaming_stats = self._streaming_client.get_statistics()

        return {
            "historical_data": historical_stats,
            "streaming": streaming_stats,
            "timestamp": datetime.now().isoformat(),
        }

    def health_check(self) -> dict[str, Any]:
        """
        Perform comprehensive health check of all components.

        Returns:
            Dictionary with health status and any issues/recommendations
        """
        health: dict[str, Any] = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "overall_issues": [],
            "overall_recommendations": [],
        }

        try:
            # Check authentication
            auth_health = self._auth_manager.health_check()
            health["components"]["authentication"] = auth_health

            # Check historical data retriever
            historical_health = self._historical_retriever.health_check()
            health["components"]["historical_data"] = historical_health

            # Check streaming client
            streaming_health = self._streaming_client.health_check()
            health["components"]["streaming"] = streaming_health

            # Aggregate issues and recommendations
            for component_health in health["components"].values():
                if component_health.get("issues"):
                    health["overall_issues"].extend(component_health["issues"])
                if component_health.get("recommendations"):
                    health["overall_recommendations"].extend(component_health["recommendations"])

            # Set overall status
            if health["overall_issues"]:
                unhealthy_count = sum(
                    1 for h in health["components"].values() if h.get("status") == "unhealthy"
                )
                if unhealthy_count > 0:
                    health["status"] = "unhealthy"
                else:
                    health["status"] = "degraded"

        except Exception as e:
            health["status"] = "error"
            health["overall_issues"].append(f"Health check failed: {e}")

        return health

    async def close(self) -> None:
        """
        Close the client and cleanup resources.

        Call this method when done using the client to properly cleanup
        connections and resources.
        """
        logger.info("Closing SchwabClient")

        try:
            await self._streaming_client.stop()
        except Exception as e:
            logger.warning(f"Error stopping streaming client: {e}")

        try:
            self._auth_manager.cleanup()
        except Exception as e:
            logger.warning(f"Error cleaning up auth manager: {e}")

        logger.info("SchwabClient closed")

    async def __aenter__(self) -> "SchwabClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


# Convenience functions for quick access
async def get_historical_data(
    symbol: str,
    api_key: str,
    app_secret: str,
    callback_url: str = "https://localhost:8080/callback",
    **kwargs: Any,
) -> pd.DataFrame | None:
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
    async with SchwabClient(api_key, app_secret, callback_url) as client:
        return await client.get_historical_data(symbol, **kwargs)


async def stream_quotes(
    symbols: str | list[str],
    callback: Callable[[str, dict[str, Any]], None],
    api_key: str,
    app_secret: str,
    duration: int | None = None,
    callback_url: str = "https://localhost:8080/callback",
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
    async with SchwabClient(api_key, app_secret, callback_url) as client:
        await client.stream_quotes(symbols, callback, duration)


# Export main classes
__all__ = ["SchwabClient", "SchwabClientError", "get_historical_data", "stream_quotes"]
