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
        
        # Token file path
        self.token_file = Path("data") / "schwab_tokens.json"
        self.token_file.parent.mkdir(exist_ok=True)
        
        logger.info("TradeAssistSchwabClient initialized")
    
    async def initialize(self) -> None:
        """
        Initialize the Schwab client with authentication.
        
        Raises:
            SchwabClientError: If initialization fails
        """
        try:
            self.client = SchwabClient(
                api_key=settings.SCHWAB_CLIENT_ID,
                app_secret=settings.SCHWAB_CLIENT_SECRET,
                callback_url=settings.SCHWAB_REDIRECT_URI,
                token_file=str(self.token_file),
            )
            
            # Perform health check
            health = self.client.health_check()
            if health["status"] != "healthy":
                logger.warning(f"Schwab client health issues: {health['issues']}")
                if health["status"] == "error":
                    raise SchwabClientError(f"Client unhealthy: {health['issues']}")
            
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
        if not self.client:
            raise SchwabClientError("Client not initialized")
            
        if not self.data_callback:
            raise SchwabClientError("Data callback not set")
        
        try:
            logger.info(f"Starting streaming for {len(symbols)} symbols: {symbols}")
            
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
            
            # Stream indefinitely with auto-reconnect
            await self.client.stream_quotes(
                symbols=symbols,
                callback=tracked_callback,
                duration=None,  # Indefinite
                auto_reconnect=True
            )
            
            return True
            
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