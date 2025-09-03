"""
Real-time WebSocket endpoints.

Provides WebSocket connections for real-time market data streaming,
alert notifications, and system status updates with <100ms delivery targets.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Set, Optional, Any, List

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..config import settings
from .message_types import (
    WebSocketMessage as TypedWebSocketMessage, OutgoingMessage,
    MarketDataMessage, MarketDataUpdate, AlertMessage, AlertNotification,
    AnalyticsMessage, AnalyticsUpdate, TechnicalIndicatorMessage, TechnicalIndicatorUpdate,
    ConnectionMessage, ConnectionStatus, ErrorMessage, ErrorDetails
)
from .message_handler import MessageHandler

logger = structlog.get_logger()
router = APIRouter()


class WebSocketMessage(BaseModel):
    """Legacy base model for WebSocket messages - kept for backward compatibility."""
    type: str
    timestamp: datetime
    data: Dict[str, Any]


class ConnectionManager:
    """
    Enhanced WebSocket connection manager with typed message support.
    
    Manages active WebSocket connections for real-time broadcasting
    of market data, alerts, and system status updates with comprehensive
    message validation and performance optimization.
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # client_id -> websocket
        self.client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> subscription types
        self.client_heartbeats: Dict[str, datetime] = {}  # client_id -> last heartbeat
        self.connection_count = 0
        self.max_connections = settings.MAX_WEBSOCKET_CONNECTIONS
        self.message_handler = MessageHandler()
        self.performance_metrics = {
            "messages_sent": 0,
            "broadcast_times": [],
            "average_broadcast_time": 0.0
        }
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 90   # seconds
        self._heartbeat_task = None
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> tuple[bool, str]:
        """
        Accept new WebSocket connection with improved stability.
        
        Args:
            websocket: WebSocket connection to accept.
            client_id: Optional client ID for the connection.

        Returns:
            tuple[bool, str]: (success, client_id)
        """
        if len(self.active_connections) >= self.max_connections:
            logger.warning(f"WebSocket connection rejected: at capacity ({self.max_connections})")
            return False, ""
        
        # Generate client ID if not provided
        if not client_id:
            client_id = f"client_{self.connection_count + 1}_{int(time.time())}"
        
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.client_subscriptions[client_id] = set()
            self.connection_count += 1
            
            logger.info(f"WebSocket connection accepted for {client_id}. Active connections: {len(self.active_connections)}")
            
            # Send welcome message in the format expected by frontend
            welcome_message = {
                "messageType": "connection_status",  # Frontend expects messageType, not type
                "version": "1.0",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "clientId": client_id,
                    "connectedAt": datetime.utcnow().isoformat(),
                    "subscriptions": [],
                    "lastHeartbeat": datetime.utcnow().isoformat(),
                    "connectionQuality": "good"
                }
            }
            
            await self.send_personal_message(websocket, welcome_message)
            
            # Initialize heartbeat tracking
            self.client_heartbeats[client_id] = datetime.utcnow()
            
            # Start heartbeat monitoring task if not already running
            if self._heartbeat_task is None or self._heartbeat_task.done():
                self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            
            return True, client_id
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            # Clean up partial connection state
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            if client_id in self.client_subscriptions:
                del self.client_subscriptions[client_id]
            return False, ""
    
    def disconnect(self, client_id: str) -> None:
        """
        Remove WebSocket connection by client ID.
        
        Args:
            client_id: Client identifier to disconnect.
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        if client_id in self.client_heartbeats:
            del self.client_heartbeats[client_id]
        logger.info(f"Client {client_id} disconnected. Active connections: {len(self.active_connections)}")
    
    def disconnect_websocket(self, websocket: WebSocket) -> None:
        """
        Remove WebSocket connection by websocket instance (backward compatibility).
        
        Args:
            websocket: WebSocket connection to remove.
        """
        client_id = None
        for cid, ws in self.active_connections.items():
            if ws == websocket:
                client_id = cid
                break
        if client_id:
            self.disconnect(client_id)
    
    async def send_personal_message(self, websocket: WebSocket, message: dict) -> bool:
        """
        Send message to specific WebSocket connection with improved error handling.
        
        Args:
            websocket: Target WebSocket connection.
            message: Message to send.
            
        Returns:
            bool: True if message sent successfully, False otherwise.
        """
        try:
            json_message = json.dumps(message, default=str)
            await websocket.send_text(json_message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            self.disconnect_websocket(websocket)
            return False
    
    async def broadcast(self, message: dict) -> int:
        """
        Broadcast message to all active connections with improved stability.
        
        Args:
            message: Message to broadcast.
            
        Returns:
            int: Number of successful broadcasts.
        """
        if not self.active_connections:
            return 0
        
        # Create JSON message once for efficiency
        json_message = json.dumps(message, default=str)
        
        # Send to all connections, remove failed ones
        disconnected_clients = set()
        successful_sends = 0
        
        for client_id, websocket in self.active_connections.copy().items():
            try:
                await websocket.send_text(json_message)
                successful_sends += 1
            except Exception as e:
                logger.warning(f"Failed to broadcast to {client_id}: {e}")
                disconnected_clients.add(client_id)
        
        # Batch cleanup failed connections
        if disconnected_clients:
            for client_id in disconnected_clients:
                self.disconnect(client_id)
            logger.info(f"Cleaned up {len(disconnected_clients)} failed connections")
        
        # Update performance metrics
        self.performance_metrics["messages_sent"] += successful_sends
        
        return successful_sends

    async def broadcast_tick_update(self, instrument_id: int, symbol: str, price: float, volume: float = 0, bid: float = None, ask: float = None, timestamp: str = None) -> int:
        """
        Broadcast market data tick update to all connected clients.
        
        Args:
            instrument_id: The instrument identifier
            symbol: The trading symbol
            price: Current price
            volume: Trading volume (default: 0)
            bid: Bid price (optional)
            ask: Ask price (optional)
            timestamp: Market data timestamp (optional)
            
        Returns:
            int: Number of successful broadcasts
        """
        if not self.active_connections:
            return 0
            
        # Create market data message in expected format
        current_timestamp = timestamp or datetime.utcnow().isoformat()
        tick_message = {
            "messageType": "market_data",
            "version": "1.0", 
            "timestamp": current_timestamp,
            "data": {
                "instrumentId": instrument_id,
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "timestamp": current_timestamp,
                "bid": bid,
                "ask": ask,
                "changePercent": None  # Calculate if needed
            }
        }
        
        return await self.broadcast(tick_message)

    async def broadcast_database_performance(self, metrics: dict) -> int:
        """
        Broadcast database performance metrics to all connected clients.
        
        Args:
            metrics: Performance metrics dictionary
            
        Returns:
            int: Number of successful broadcasts
        """
        if not self.active_connections:
            return 0
            
        performance_message = {
            "messageType": "database_performance",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(), 
            "data": metrics
        }
        
        return await self.broadcast(performance_message)

    async def handle_client_message(self, websocket: WebSocket, client_id: str, message: dict) -> None:
        """
        Handle incoming messages from WebSocket clients.
        
        Args:
            websocket: The WebSocket connection
            client_id: The client identifier
            message: The parsed message dictionary
        """
        try:
            message_type = message.get("messageType", message.get("type", ""))  # Support both formats
            
            if message_type == "ping":
                # Update heartbeat timestamp
                self.client_heartbeats[client_id] = datetime.utcnow()
                
                # Respond to ping with pong
                pong_message = {
                    "messageType": "pong",
                    "version": "1.0",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "clientTime": message.get("data", {}).get("clientTime", datetime.utcnow().isoformat()),
                        "serverTime": datetime.utcnow().isoformat(),
                        "sequence": message.get("data", {}).get("sequence"),
                        "latencyMs": 0  # Calculate if needed
                    }
                }
                await self.send_personal_message(websocket, pong_message)
                
            elif message_type == "subscribe":
                # Handle subscription requests
                data = message.get("data", {})
                subscription_type = data.get("subscriptionType", "")
                instrument_id = data.get("instrumentId")
                request_id = data.get("requestId", f"req_{int(time.time())}")
                
                if client_id not in self.client_subscriptions:
                    self.client_subscriptions[client_id] = set()
                
                subscription_key = f"{subscription_type}_{instrument_id}" if instrument_id else subscription_type
                self.client_subscriptions[client_id].add(subscription_key)
                
                # Send subscription acknowledgment
                response = {
                    "messageType": "subscription_ack",
                    "version": "1.0",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "subscriptionType": subscription_type,
                        "instrumentId": instrument_id,
                        "status": "subscribed",
                        "requestId": request_id
                    }
                }
                await self.send_personal_message(websocket, response)
                
            else:
                # Unknown message type
                error_response = {
                    "messageType": "error",
                    "version": "1.0",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "errorCode": "UNKNOWN_MESSAGE_TYPE",
                        "errorMessage": f"Unknown message type: {message_type}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "severity": "warning"
                    }
                }
                await self.send_personal_message(websocket, error_response)
                
        except Exception as e:
            logger.error(f"Error handling client message from {client_id}: {e}")
            error_response = {
                "messageType": "error",
                "version": "1.0",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "errorCode": "MESSAGE_HANDLING_ERROR",
                    "errorMessage": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "error"
                }
            }
            await self.send_personal_message(websocket, error_response)

    async def _heartbeat_monitor(self):
        """
        Monitor client heartbeats and disconnect stale connections.
        This runs as a background task to maintain connection health.
        """
        while self.active_connections:
            try:
                now = datetime.utcnow()
                stale_clients = []
                
                for client_id, last_heartbeat in self.client_heartbeats.items():
                    time_since_heartbeat = (now - last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > self.heartbeat_timeout:
                        stale_clients.append(client_id)
                        logger.warning(f"Client {client_id} heartbeat timeout: {time_since_heartbeat}s")
                
                # Disconnect stale clients
                for client_id in stale_clients:
                    self.disconnect(client_id)
                
                # Wait before next check
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """
    Enhanced WebSocket endpoint for real-time data and alert streaming.
    
    Provides real-time streaming of market data, alerts, and system status
    with <50ms delivery target for connected clients using typed message system.
    
    Args:
        websocket: WebSocket connection.
    """
    # Attempt to accept connection with client ID
    connection_accepted, client_id = await manager.connect(websocket)
    
    if not connection_accepted:
        await websocket.close(code=1000, reason="Server at capacity")
        return
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping, subscription requests, etc.)
                data = await websocket.receive_text()
                
                # Parse client message
                try:
                    client_message = json.loads(data)
                    await manager.handle_client_message(websocket, client_id, client_message)
                except json.JSONDecodeError:
                    error_msg = {
                        "messageType": "error",
                        "version": "1.0",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {
                            "errorCode": "INVALID_JSON",
                            "errorMessage": "Invalid JSON format",
                            "severity": "error"
                        }
                    }
                    await manager.send_personal_message(websocket, error_msg)
                
            except WebSocketDisconnect:
                break
            
            except Exception as e:
                logger.error(f"WebSocket error for client {client_id}: {e}")
                error_msg = {
                    "messageType": "error",
                    "version": "1.0",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "errorCode": "INTERNAL_ERROR",
                        "errorMessage": "Internal server error",
                        "severity": "critical"
                    }
                }
                await manager.send_personal_message(websocket, error_msg)
                break
    
    finally:
        manager.disconnect(client_id)


# Export manager for use by other services
def get_websocket_manager() -> ConnectionManager:
    """
    Get the enhanced global WebSocket connection manager.
    
    Returns:
        ConnectionManager: Enhanced global connection manager instance with typed message support.
    """
    return manager


# Performance monitoring endpoint for connection manager
def get_websocket_performance_metrics() -> Dict[str, Any]:
    """
    Get comprehensive WebSocket performance metrics.
    
    Returns:
        Dictionary containing connection and message processing metrics.
    """
    return {
        "total_connections": len(manager.active_connections),
        "messages_sent": manager.performance_metrics["messages_sent"],
        "connection_health": manager.get_connection_health_status() if hasattr(manager, 'get_connection_health_status') else {}
    }