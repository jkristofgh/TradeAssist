"""
Schwab API Integration using schwab-package.

Provides real-time market data streaming and authentication
using the proven schwab-package wrapper around schwab-py.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

import structlog
from schwab_package import SchwabClient, SchwabClientError

from ..config import settings
from ..services.secret_manager import secret_manager
from ..services.circuit_breaker import circuit_breaker, CircuitBreakerConfig, circuit_manager

logger = structlog.get_logger()


class TradeAssistSchwabClient:
    """
    TradeAssist integration with schwab-package.
    
    Provides real-time market data streaming and authentication
    for the TradeAssist alert system using the mature schwab-package.
    """
    
    def __init__(self):
        self.client: Optional[SchwabClient] = None
        self.data_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
        self.is_connected = False
        self.is_streaming = False
        
        # Performance tracking
        self._message_count = 0
        self._start_time: Optional[datetime] = None
        self._last_message_time: Optional[datetime] = None
        
        # Circuit breaker configuration
        self._circuit_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            success_threshold=2,
            request_timeout=10.0,
            error_percentage=60.0
        )
        
        # Token file path
        self.token_file = Path("data") / "schwab_tokens.json"
        self.token_file.parent.mkdir(exist_ok=True)
        
        logger.info("TradeAssistSchwabClient initialized")
    
    async def initialize(self) -> None:
        """
        Initialize the Schwab client with authentication.
        Uses Google Cloud Secret Manager for secure credential retrieval.
        
        Raises:
            SchwabClientError: If initialization fails
        """
        try:
            # Check if running in demo mode
            if settings.DEMO_MODE or settings.SCHWAB_CLIENT_ID == "demo_mode":
                logger.info("Running in demo mode - Schwab client will simulate data")
                self.is_connected = True
                return
            
            # Get credentials from Secret Manager with fallback to config
            credentials = await secret_manager.get_schwab_credentials()
            
            api_key = credentials.get("app_key") or settings.SCHWAB_CLIENT_ID
            app_secret = credentials.get("app_secret") or settings.SCHWAB_CLIENT_SECRET
            
            if not api_key or not app_secret:
                raise SchwabClientError(
                    "Schwab API credentials not found in Secret Manager or environment variables"
                )
            
            logger.info("Initializing Schwab client with secure credentials")
            
            self.client = SchwabClient(
                api_key=api_key,
                app_secret=app_secret,
                callback_url=settings.SCHWAB_REDIRECT_URI,
                token_file=str(self.token_file),
            )
            
            # Perform health check
            health = self.client.health_check()
            if health.get("status") != "healthy":
                issues = health.get('issues', 'Unknown issues')
                logger.warning(f"Schwab client health issues: {issues}")
                if health.get("status") == "error":
                    raise SchwabClientError(f"Client unhealthy: {issues}")
            
            self.is_connected = True
            logger.info("Schwab client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Schwab client: {e}")
            raise
    
    def set_data_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Set callback function for market data updates.
        
        Args:
            callback: Function called with (symbol, data) for each market update
        """
        self.data_callback = callback
        logger.debug("Data callback set")
    
    @circuit_breaker("schwab_streaming")
    async def _start_streaming_with_circuit_breaker(self, symbols: List[str]) -> bool:
        """Start streaming with circuit breaker protection (internal method)."""
        # Create callback wrapper for performance tracking
        def tracked_callback(symbol: str, data: Dict[str, Any]) -> None:
            self._message_count += 1
            self._last_message_time = datetime.utcnow()
            
            # Call the registered callback
            if self.data_callback:
                self.data_callback(symbol, data)
        
        # Start streaming using schwab-package
        self._start_time = datetime.utcnow()
        self.is_streaming = True
        
        # Start streaming in background task - don't await it
        asyncio.create_task(self.client.stream_quotes(
            symbols=symbols,
            callback=tracked_callback,
            duration=None,  # Indefinite
            auto_reconnect=True
        ))
        
        # Return immediately to avoid circuit breaker timeout
        return True
    
    async def start_streaming(self, symbols: List[str]) -> bool:
        """
        Start real-time streaming for specified symbols.
        
        Args:
            symbols: List of symbols to stream (e.g., ["/ES", "SPY", "^VIX"])
            
        Returns:
            bool: True if streaming started successfully
            
        Raises:
            SchwabClientError: If streaming fails to start
        """
        # Handle demo mode
        if settings.DEMO_MODE or settings.SCHWAB_CLIENT_ID == "demo_mode":
            logger.info(f"Demo mode: Simulating streaming for {len(symbols)} symbols: {symbols}")
            self.is_streaming = True
            return True
            
        if not self.client:
            raise SchwabClientError("Client not initialized")
            
        if not self.data_callback:
            raise SchwabClientError("Data callback not set")
        
        try:
            logger.info(f"Starting streaming for {len(symbols)} symbols: {symbols}")
            
            # Use circuit breaker for streaming
            return await self._start_streaming_with_circuit_breaker(symbols)
            
        except Exception as e:
            self.is_streaming = False
            logger.error(f"Failed to start streaming: {e}")
            raise SchwabClientError(f"Streaming failed: {e}") from e
    
    async def stop_streaming(self) -> None:
        """Stop real-time streaming."""
        if self.client and self.is_streaming:
            try:
                logger.info("Stopping streaming")
                # The schwab-package client handles stopping via context management
                # or by ending the stream_quotes call
                self.is_streaming = False
                logger.info("Streaming stopped")
            except Exception as e:
                logger.error(f"Error stopping streaming: {e}")
    
    @circuit_breaker("schwab_auth")
    async def authenticate_manual(self) -> None:
        """
        Perform manual OAuth authentication flow.
        
        This should be called once to set up authentication.
        After that, the client handles token refresh automatically.
        """
        if not self.client:
            raise SchwabClientError("Client not initialized")
        
        try:
            logger.info("Starting manual authentication")
            self.client.authenticate_manual()
            logger.info("Manual authentication completed")
        except Exception as e:
            logger.error(f"Manual authentication failed: {e}")
            raise SchwabClientError(f"Authentication failed: {e}") from e
    
    def analyze_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze symbol to determine instrument type and characteristics.
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Dict with analysis results including instrument_type, confidence, etc.
        """
        if not self.client:
            return {"instrument_type": "unknown", "confidence": 0.0}
        
        try:
            return self.client.analyze_symbol(symbol)
        except Exception as e:
            logger.warning(f"Symbol analysis failed for {symbol}: {e}")
            return {"instrument_type": "unknown", "confidence": 0.0}
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status.
        
        Returns:
            Dict with health status and performance metrics
        """
        if not self.client:
            return {
                "status": "not_initialized",
                "client_ready": False,
                "streaming": False,
                "message_count": self._message_count,
            }
        
        # Get schwab-package health check
        health = self.client.health_check()
        
        # Add TradeAssist-specific metrics
        health.update({
            "client_ready": self.is_connected,
            "streaming": self.is_streaming,
            "message_count": self._message_count,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "last_message_time": self._last_message_time.isoformat() if self._last_message_time else None,
        })
        
        # Calculate session duration
        if self._start_time:
            session_duration = datetime.utcnow() - self._start_time
            health["session_duration_seconds"] = int(session_duration.total_seconds())
        
        # Add circuit breaker status
        health["circuit_breakers"] = {
            "streaming": circuit_manager.get_or_create("schwab_streaming").get_status(),
            "auth": circuit_manager.get_or_create("schwab_auth").get_status(),
        }
        
        return health
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get request and streaming statistics.
        
        Returns:
            Dict with comprehensive statistics
        """
        if not self.client:
            return {"error": "Client not initialized"}
        
        try:
            # Get schwab-package statistics
            stats = self.client.get_request_statistics()
            
            # Add TradeAssist metrics
            stats.update({
                "trade_assist_metrics": {
                    "message_count": self._message_count,
                    "streaming_active": self.is_streaming,
                    "connection_ready": self.is_connected,
                    "session_start": self._start_time.isoformat() if self._start_time else None,
                }
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}
    
    async def close(self) -> None:
        """Close the client and cleanup resources."""
        logger.info("Closing TradeAssist Schwab client")
        
        try:
            if self.is_streaming:
                await self.stop_streaming()
            
            if self.client:
                await self.client.close()
            
            self.is_connected = False
            logger.info("Schwab client closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing client: {e}")


# Factory function for easy initialization
async def create_schwab_client() -> TradeAssistSchwabClient:
    """
    Create and initialize a TradeAssist Schwab client.
    
    Returns:
        Initialized TradeAssistSchwabClient instance
        
    Raises:
        SchwabClientError: If initialization fails
    """
    client = TradeAssistSchwabClient()
    await client.initialize()
    return client


# Backwards compatibility - maintain existing interface
class SchwabRealTimeClient:
    """
    Backwards compatibility wrapper for existing code.
    
    Maintains the same interface as the previous custom implementation
    while using the new schwab-package backend.
    """
    
    def __init__(self):
        self._client = TradeAssistSchwabClient()
        self.data_callback: Optional[Callable] = None
        self.is_connected = False
    
    def set_data_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Set data callback (backwards compatibility)."""
        self.data_callback = callback
        self._client.set_data_callback(callback)
    
    async def start_streaming(self, symbols: List[str]) -> bool:
        """Start streaming (backwards compatibility)."""
        await self._client.initialize()
        self.is_connected = True
        return await self._client.start_streaming(symbols)
    
    async def stop_streaming(self) -> None:
        """Stop streaming (backwards compatibility)."""
        await self._client.stop_streaming()
        self.is_connected = False
    
    async def close(self) -> None:
        """Close client (backwards compatibility)."""
        await self._client.close()
        self.is_connected = False


__all__ = [
    "TradeAssistSchwabClient",
    "SchwabRealTimeClient", 
    "create_schwab_client",
    "SchwabClientError",
    # Backwards compatibility alias
    "SchwabAPIError",  # = SchwabClientError
]

# Backwards compatibility alias
SchwabAPIError = SchwabClientError