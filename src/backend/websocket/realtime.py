"""
Real-time WebSocket endpoints.

Provides WebSocket connections for real-time market data streaming,
alert notifications, and system status updates with <100ms delivery targets.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set, Optional, Any, List

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

    # Phase 3: Historical Data WebSocket Integration
    
    async def broadcast_historical_data_progress(
        self,
        query_id: str,
        symbol: str,
        progress_percent: float,
        current_step: str,
        estimated_completion: Optional[datetime] = None
    ) -> None:
        """Broadcast progress updates for historical data queries."""
        
        message = WebSocketMessage(
            type="historical_data_progress",
            timestamp=datetime.now(),
            data={
                "query_id": query_id,
                "symbol": symbol,
                "progress_percent": progress_percent,
                "current_step": current_step,
                "estimated_completion": estimated_completion.isoformat() if estimated_completion else None,
                "status": "in_progress"
            }
        )
        
        await self.broadcast(message)
        
        logger.debug(f"Historical data progress broadcasted: {symbol} {progress_percent}%")
    
    async def broadcast_historical_data_complete(
        self,
        query_id: str,
        symbol: str,
        bars_retrieved: int,
        execution_time_ms: float,
        cache_hit: bool = False
    ) -> None:
        """Broadcast completion of historical data query."""
        
        message = WebSocketMessage(
            type="historical_data_complete",
            timestamp=datetime.now(),
            data={
                "query_id": query_id,
                "symbol": symbol,
                "bars_retrieved": bars_retrieved,
                "execution_time_ms": execution_time_ms,
                "cache_hit": cache_hit,
                "status": "complete"
            }
        )
        
        await self.broadcast(message)
        
        logger.info(f"Historical data query completed: {symbol} - {bars_retrieved} bars")
    
    async def broadcast_historical_data_error(
        self,
        query_id: str,
        symbol: str,
        error_message: str,
        error_type: str = "general"
    ) -> None:
        """Broadcast historical data query error."""
        
        message = WebSocketMessage(
            type="historical_data_error",
            timestamp=datetime.now(),
            data={
                "query_id": query_id,
                "symbol": symbol,
                "error_message": error_message,
                "error_type": error_type,
                "status": "error"
            }
        )
        
        await self.broadcast(message)
        
        logger.error(f"Historical data query error broadcasted: {symbol} - {error_message}")
    
    async def broadcast_aggregation_progress(
        self,
        aggregation_id: str,
        symbol: str,
        source_frequency: str,
        target_frequency: str,
        progress_percent: float
    ) -> None:
        """Broadcast progress updates for data aggregation operations."""
        
        message = WebSocketMessage(
            type="aggregation_progress",
            timestamp=datetime.now(),
            data={
                "aggregation_id": aggregation_id,
                "symbol": symbol,
                "source_frequency": source_frequency,
                "target_frequency": target_frequency,
                "progress_percent": progress_percent,
                "status": "aggregating"
            }
        )
        
        await self.broadcast(message)
        
        logger.debug(f"Aggregation progress: {symbol} {source_frequency}→{target_frequency} {progress_percent}%")
    
    async def broadcast_aggregation_complete(
        self,
        aggregation_id: str,
        symbol: str,
        source_frequency: str,
        target_frequency: str,
        source_bars: int,
        target_bars: int,
        execution_time_ms: float
    ) -> None:
        """Broadcast completion of data aggregation."""
        
        message = WebSocketMessage(
            type="aggregation_complete",
            timestamp=datetime.now(),
            data={
                "aggregation_id": aggregation_id,
                "symbol": symbol,
                "source_frequency": source_frequency,
                "target_frequency": target_frequency,
                "source_bars": source_bars,
                "target_bars": target_bars,
                "compression_ratio": round(target_bars / source_bars if source_bars > 0 else 0, 2),
                "execution_time_ms": execution_time_ms,
                "status": "complete"
            }
        )
        
        await self.broadcast(message)
        
        logger.info(f"Aggregation completed: {symbol} {source_bars}→{target_bars} bars in {execution_time_ms}ms")
    
    async def broadcast_cache_performance_update(
        self,
        cache_hit_rate: float,
        total_requests: int,
        redis_available: bool
    ) -> None:
        """Broadcast cache performance metrics for monitoring."""
        
        message = WebSocketMessage(
            type="cache_performance",
            timestamp=datetime.now(),
            data={
                "cache_hit_rate": cache_hit_rate,
                "total_requests": total_requests,
                "redis_available": redis_available,
                "status": "healthy" if cache_hit_rate > 50 else "degraded"
            }
        )
        
        await self.broadcast(message)
        
        logger.debug(f"Cache performance update: {cache_hit_rate}% hit rate")

    
    async def broadcast_database_performance(self, performance_data: Dict[str, Any]) -> None:
        """
        Broadcast real-time database performance metrics to all connected clients.
        
        Args:
            performance_data: Database performance metrics including connection pool,
                            INSERT rates, query performance, and partition health.
        """
        message = {
            "type": "database_performance",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "connection_pool": performance_data.get("connection_pool", {}),
                "performance_metrics": performance_data.get("performance_metrics", {}),
                "partition_health": performance_data.get("partition_health", {}),
                "alerts": performance_data.get("alerts", []),
                "overall_status": performance_data.get("status", "unknown")
            }
        }
        
        await self.broadcast(message)
        logger.debug("Broadcasted database performance update", 
                    active_connections=self.connection_count,
                    status=performance_data.get("status"))
    
    async def broadcast_performance_alert(self, alert_type: str, message: str, 
                                        severity: str = "warning") -> None:
        """
        Broadcast performance-related alerts to connected clients.
        
        Args:
            alert_type: Type of performance alert (connection_pool, slow_query, etc.)
            message: Alert message description
            severity: Alert severity level (info, warning, critical)
        """
        alert_message = {
            "type": "performance_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "source": "database_performance"
            }
        }
        
        await self.broadcast(alert_message)
        logger.info(f"Broadcasted performance alert: {alert_type}", 
                   message=message, severity=severity)
    
    async def broadcast_partition_status_update(self, partition_data: Dict[str, Any]) -> None:
        """
        Broadcast partition status updates to connected clients.
        
        Args:
            partition_data: Partition status information including health,
                          storage utilization, and maintenance status.
        """
        message = {
            "type": "partition_status",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "service_status": partition_data.get("service_status", "unknown"),
                "partitions": partition_data.get("partitions", {}),
                "health_summary": partition_data.get("health_summary", {}),
                "config": partition_data.get("config", {}),
                "recent_activity": partition_data.get("recent_activity", [])
            }
        }
        
        await self.broadcast(message)
        logger.debug("Broadcasted partition status update", 
                    total_partitions=partition_data.get("health_summary", {}).get("total_partitions", 0))
    
    async def broadcast_performance_benchmark_results(self, benchmark_data: Dict[str, Any]) -> None:
        """
        Broadcast performance benchmark test results to connected clients.
        
        Args:
            benchmark_data: Performance benchmark results including INSERT rates,
                          calculation speedup, and capacity validation.
        """
        message = {
            "type": "performance_benchmark",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "insert_performance": benchmark_data.get("insert_performance", {}),
                "calculation_performance": benchmark_data.get("calculation_performance", {}),
                "capacity_test": benchmark_data.get("capacity_test", {}),
                "baseline_comparison": benchmark_data.get("baseline_comparison", {}),
                "test_status": benchmark_data.get("test_status", "unknown")
            }
        }
        
        await self.broadcast(message)
        logger.info("Broadcasted performance benchmark results", 
                   test_status=benchmark_data.get("test_status"))
    
    async def send_historical_data_stream(
        self,
        websocket,
        query_id: str,
        symbol: str,
        bars_data: List[Dict[str, Any]],
        chunk_size: int = 100
    ) -> None:
        """Stream historical data in chunks to a specific WebSocket connection."""
        
        try:
            total_bars = len(bars_data)
            chunks_sent = 0
            
            # Send data in chunks to prevent overwhelming the connection
            for i in range(0, total_bars, chunk_size):
                chunk = bars_data[i:i + chunk_size]
                chunk_number = chunks_sent + 1
                total_chunks = (total_bars + chunk_size - 1) // chunk_size
                
                message = WebSocketMessage(
                    type="historical_data_chunk",
                    timestamp=datetime.now(),
                    data={
                        "query_id": query_id,
                        "symbol": symbol,
                        "chunk_number": chunk_number,
                        "total_chunks": total_chunks,
                        "bars": chunk,
                        "is_final_chunk": chunk_number == total_chunks
                    }
                )
                
                await self.send_personal_message(websocket, message)
                chunks_sent += 1
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
            
            logger.info(f"Streamed {total_bars} bars in {chunks_sent} chunks for {symbol}")
            
        except Exception as e:
            logger.error(f"Error streaming historical data for {symbol}: {e}")
            await self.broadcast_historical_data_error(
                query_id, symbol, f"Streaming error: {str(e)}", "streaming_error"
            )


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