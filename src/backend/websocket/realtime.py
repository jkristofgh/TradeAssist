"""
Real-time WebSocket endpoints.

Provides WebSocket connections for real-time market data streaming,
alert notifications, and system status updates with <100ms delivery targets.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set, Optional, Any

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..config import settings

logger = structlog.get_logger()
router = APIRouter()


class WebSocketMessage(BaseModel):
    """Base model for WebSocket messages."""
    type: str
    timestamp: datetime
    data: Dict[str, Any]


class ConnectionManager:
    """
    WebSocket connection manager.
    
    Manages active WebSocket connections for real-time broadcasting
    of market data, alerts, and system status updates.
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_count = 0
        self.max_connections = settings.MAX_WEBSOCKET_CONNECTIONS
    
    async def connect(self, websocket: WebSocket) -> bool:
        """
        Accept new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to accept.
        
        Returns:
            bool: True if connection accepted, False if at capacity.
        """
        if len(self.active_connections) >= self.max_connections:
            logger.warning(f"WebSocket connection rejected: at capacity ({self.max_connections})")
            return False
        
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_count += 1
        
        logger.info(f"WebSocket connection accepted. Active connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_personal_message(websocket, {
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "connection_id": self.connection_count,
                "server_time": datetime.utcnow().isoformat(),
                "active_connections": len(self.active_connections)
            }
        })
        
        return True
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket connection removed. Active connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, websocket: WebSocket, message: dict) -> None:
        """
        Send message to specific WebSocket connection.
        
        Args:
            websocket: Target WebSocket connection.
            message: Message to send.
        """
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict) -> None:
        """
        Broadcast message to all active connections.
        
        Args:
            message: Message to broadcast.
        """
        if not self.active_connections:
            return
        
        # Create JSON message once for efficiency
        json_message = json.dumps(message, default=str)
        
        # Send to all connections, remove failed ones
        disconnected_connections = set()
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json_message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to connection: {e}")
                disconnected_connections.add(connection)
        
        # Remove failed connections
        for connection in disconnected_connections:
            self.disconnect(connection)
        
        if disconnected_connections:
            logger.info(f"Removed {len(disconnected_connections)} failed connections")
    
    async def broadcast_tick_update(self, instrument_id: int, symbol: str, price: float, volume: int, timestamp: datetime) -> None:
        """
        Broadcast market tick update.
        
        Args:
            instrument_id: Instrument ID.
            symbol: Instrument symbol.
            price: Current price.
            volume: Trade volume.
            timestamp: Tick timestamp.
        """
        message = {
            "type": "tick_update",
            "timestamp": timestamp.isoformat(),
            "data": {
                "instrument_id": instrument_id,
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "timestamp": timestamp.isoformat()
            }
        }
        await self.broadcast(message)
    
    async def broadcast_alert_fired(
        self,
        rule_id: int,
        instrument_id: int,
        symbol: str,
        trigger_value: float,
        threshold_value: float,
        condition: str,
        timestamp: datetime,
        evaluation_time_ms: Optional[int] = None
    ) -> None:
        """
        Broadcast alert firing notification.
        
        Args:
            rule_id: Rule ID that fired.
            instrument_id: Instrument ID.
            symbol: Instrument symbol.
            trigger_value: Value that triggered the alert.
            threshold_value: Threshold from the rule.
            condition: Rule condition.
            timestamp: Alert timestamp.
            evaluation_time_ms: Rule evaluation time.
        """
        message = {
            "type": "alert_fired",
            "timestamp": timestamp.isoformat(),
            "data": {
                "rule_id": rule_id,
                "instrument_id": instrument_id,
                "symbol": symbol,
                "trigger_value": trigger_value,
                "threshold_value": threshold_value,
                "condition": condition,
                "timestamp": timestamp.isoformat(),
                "evaluation_time_ms": evaluation_time_ms
            }
        }
        await self.broadcast(message)
    
    async def broadcast_health_status(self, status: dict) -> None:
        """
        Broadcast system health status.
        
        Args:
            status: Health status data.
        """
        message = {
            "type": "health_status",
            "timestamp": datetime.utcnow().isoformat(),
            "data": status
        }
        await self.broadcast(message)
    
    async def broadcast_rule_triggered(self, rule_id: int, match_details: dict, evaluation_time: int) -> None:
        """
        Broadcast rule trigger notification.
        
        Args:
            rule_id: Rule ID that triggered.
            match_details: Rule match details.
            evaluation_time: Evaluation time in milliseconds.
        """
        message = {
            "type": "rule_triggered",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "rule_id": rule_id,
                "match_details": match_details,
                "evaluation_time": evaluation_time
            }
        }
        await self.broadcast(message)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time data and alert streaming.
    
    Provides real-time streaming of market data, alerts, and system status
    with <100ms delivery target for connected clients.
    
    Args:
        websocket: WebSocket connection.
    """
    # Attempt to accept connection
    connection_accepted = await manager.connect(websocket)
    
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
                    await handle_client_message(websocket, client_message)
                except json.JSONDecodeError:
                    await manager.send_personal_message(websocket, {
                        "type": "error",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {
                            "message": "Invalid JSON format",
                            "received": data
                        }
                    })
                
            except WebSocketDisconnect:
                break
            
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await manager.send_personal_message(websocket, {
                    "type": "error",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "message": "Internal server error",
                        "error": str(e)
                    }
                })
                break
    
    finally:
        manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, message: dict) -> None:
    """
    Handle incoming client WebSocket messages.
    
    Args:
        websocket: Client WebSocket connection.
        message: Parsed client message.
    """
    message_type = message.get("type", "unknown")
    
    if message_type == "ping":
        # Respond to ping with pong
        await manager.send_personal_message(websocket, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"server_time": datetime.utcnow().isoformat()}
        })
    
    elif message_type == "subscribe":
        # Handle subscription requests (future enhancement)
        await manager.send_personal_message(websocket, {
            "type": "subscription_acknowledged",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "subscribed_to": message.get("data", {}),
                "status": "active"
            }
        })
    
    else:
        # Unknown message type
        await manager.send_personal_message(websocket, {
            "type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "message": f"Unknown message type: {message_type}",
                "supported_types": ["ping", "subscribe"]
            }
        })


# Export manager for use by other services
def get_websocket_manager() -> ConnectionManager:
    """
    Get the global WebSocket connection manager.
    
    Returns:
        ConnectionManager: Global connection manager instance.
    """
    return manager