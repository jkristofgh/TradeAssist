"""
WebSocket Message Handler

Handles WebSocket message validation, routing, and processing with
comprehensive error handling and performance optimization.
"""

import json
import time
import structlog
from fastapi import WebSocket
from typing import Dict, Any, Optional, Union, Callable
from datetime import datetime
from pydantic import ValidationError

from .message_types import (
    WebSocketMessage, AllMessages, IncomingMessage, OutgoingMessage,
    MESSAGE_TYPE_REGISTRY, MessageVersion,
    ErrorMessage, ErrorDetails, PongMessage, PongData,
    SubscriptionAckMessage, SubscriptionAcknowledgment
)

logger = structlog.get_logger()


class MessageHandler:
    """Handles WebSocket message validation, routing, and processing."""
    
    def __init__(self):
        self.message_validators = MESSAGE_TYPE_REGISTRY.copy()
        self.message_handlers: Dict[str, Callable] = {}
        self.performance_metrics = {
            "total_messages": 0,
            "validation_errors": 0,
            "processing_times": [],
            "average_processing_time": 0.0
        }
    
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register a handler function for a specific message type.
        
        Args:
            message_type: Message type to handle.
            handler: Callable handler function.
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type: {message_type}")
    
    async def validate_message(self, message_data: Dict[str, Any]) -> Optional[WebSocketMessage]:
        """
        Validate incoming message against appropriate schema.
        
        Args:
            message_data: Raw message data to validate.
            
        Returns:
            Validated message object or None if validation fails.
        """
        start_time = time.perf_counter()
        
        try:
            message_type = message_data.get("message_type")
            if not message_type:
                logger.warning("Message missing message_type field", data=message_data)
                self.performance_metrics["validation_errors"] += 1
                return None
            
            validator_class = self.message_validators.get(message_type)
            if not validator_class:
                logger.warning(f"Unknown message type: {message_type}", data=message_data)
                self.performance_metrics["validation_errors"] += 1
                return None
            
            # Validate message structure
            validated_message = validator_class(**message_data)
            
            # Record performance metrics
            processing_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
            self.performance_metrics["processing_times"].append(processing_time)
            self.performance_metrics["total_messages"] += 1
            
            # Keep only last 1000 processing times for average calculation
            if len(self.performance_metrics["processing_times"]) > 1000:
                self.performance_metrics["processing_times"] = \
                    self.performance_metrics["processing_times"][-1000:]
            
            # Update average processing time
            self.performance_metrics["average_processing_time"] = \
                sum(self.performance_metrics["processing_times"]) / len(self.performance_metrics["processing_times"])
            
            logger.debug(
                f"Message validated successfully",
                message_type=message_type,
                processing_time_ms=processing_time,
                average_processing_time_ms=self.performance_metrics["average_processing_time"]
            )
            
            return validated_message
            
        except ValidationError as e:
            logger.error(f"Message validation failed: {e}", message_data=message_data)
            self.performance_metrics["validation_errors"] += 1
            return None
        except Exception as e:
            logger.error(f"Unexpected validation error: {e}", message_data=message_data)
            self.performance_metrics["validation_errors"] += 1
            return None
    
    async def process_message(
        self, 
        websocket: WebSocket, 
        message: WebSocketMessage,
        client_id: str
    ) -> Optional[WebSocketMessage]:
        """
        Process validated message and return response if needed.
        
        Args:
            websocket: Client WebSocket connection.
            message: Validated message object.
            client_id: Client identifier.
            
        Returns:
            Response message if applicable, None otherwise.
        """
        try:
            message_type = message.message_type
            
            # Handle built-in message types
            if message_type == "ping":
                return await self._handle_ping_message(message)
            
            elif message_type == "subscribe":
                return await self._handle_subscription_message(message, client_id)
            
            elif message_type == "unsubscribe":
                return await self._handle_unsubscription_message(message, client_id)
            
            # Handle custom registered message types
            elif message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                return await handler(websocket, message, client_id)
            
            else:
                logger.warning(f"No handler registered for message type: {message_type}")
                return await self.create_error_message(
                    "NO_HANDLER",
                    f"No handler available for message type: {message_type}",
                    getattr(message.data, 'request_id', None)
                )
                
        except Exception as e:
            logger.error(f"Message processing error: {e}", message_type=message.message_type)
            return await self.create_error_message(
                "PROCESSING_ERROR",
                f"Failed to process message: {str(e)}",
                getattr(message.data, 'request_id', None)
            )
    
    async def _handle_ping_message(self, message: WebSocketMessage) -> PongMessage:
        """Handle ping message and return pong response."""
        ping_data = message.data
        server_time = datetime.utcnow()
        
        # Calculate latency if client_time is provided
        latency_ms = None
        if hasattr(ping_data, 'client_time'):
            try:
                client_time = ping_data.client_time
                if isinstance(client_time, str):
                    client_time = datetime.fromisoformat(client_time.replace('Z', '+00:00'))
                latency_ms = (server_time - client_time).total_seconds() * 1000
            except Exception as e:
                logger.warning(f"Failed to calculate latency: {e}")
        
        return PongMessage(
            data=PongData(
                client_time=ping_data.client_time,
                server_time=server_time,
                sequence=getattr(ping_data, 'sequence', None),
                latency_ms=latency_ms
            )
        )
    
    async def _handle_subscription_message(
        self, 
        message: WebSocketMessage, 
        client_id: str
    ) -> SubscriptionAckMessage:
        """Handle subscription request."""
        sub_data = message.data
        
        # TODO: Implement actual subscription logic with connection manager
        logger.info(
            f"Subscription request from {client_id}",
            subscription_type=sub_data.subscription_type,
            instrument_id=getattr(sub_data, 'instrument_id', None)
        )
        
        return SubscriptionAckMessage(
            data=SubscriptionAcknowledgment(
                subscription_type=sub_data.subscription_type,
                instrument_id=getattr(sub_data, 'instrument_id', None),
                status="subscribed",
                message="Subscription successful",
                request_id=getattr(sub_data, 'request_id', None)
            )
        )
    
    async def _handle_unsubscription_message(
        self, 
        message: WebSocketMessage, 
        client_id: str
    ) -> SubscriptionAckMessage:
        """Handle unsubscription request."""
        unsub_data = message.data
        
        # TODO: Implement actual unsubscription logic with connection manager
        logger.info(
            f"Unsubscription request from {client_id}",
            subscription_type=unsub_data.subscription_type,
            instrument_id=getattr(unsub_data, 'instrument_id', None)
        )
        
        return SubscriptionAckMessage(
            data=SubscriptionAcknowledgment(
                subscription_type=unsub_data.subscription_type,
                instrument_id=getattr(unsub_data, 'instrument_id', None),
                status="unsubscribed",
                message="Unsubscription successful",
                request_id=getattr(unsub_data, 'request_id', None)
            )
        )
    
    async def create_error_message(
        self, 
        error_code: str, 
        error_message: str,
        request_id: Optional[str] = None,
        severity: str = "error"
    ) -> ErrorMessage:
        """Create standardized error message."""
        return ErrorMessage(
            data=ErrorDetails(
                error_code=error_code,
                error_message=error_message,
                request_id=request_id,
                timestamp=datetime.utcnow(),
                severity=severity
            )
        )
    
    async def serialize_message(self, message: WebSocketMessage) -> str:
        """
        Serialize message to JSON string with performance optimization.
        
        Args:
            message: Message to serialize.
            
        Returns:
            JSON string representation.
        """
        start_time = time.perf_counter()
        
        try:
            # Use pydantic's optimized JSON serialization
            json_str = message.json()
            
            # Record serialization performance
            serialization_time = (time.perf_counter() - start_time) * 1000
            
            if serialization_time > 10:  # Log if serialization takes >10ms
                logger.warning(
                    f"Slow message serialization",
                    message_type=message.message_type,
                    serialization_time_ms=serialization_time
                )
            
            return json_str
            
        except Exception as e:
            logger.error(f"Message serialization failed: {e}")
            error_msg = await self.create_error_message(
                "SERIALIZATION_ERROR",
                f"Failed to serialize message: {str(e)}"
            )
            return error_msg.json()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            **self.performance_metrics,
            "validation_error_rate": (
                self.performance_metrics["validation_errors"] / 
                max(self.performance_metrics["total_messages"], 1)
            ) * 100
        }
    
    def reset_performance_metrics(self) -> None:
        """Reset performance metrics for fresh monitoring."""
        self.performance_metrics = {
            "total_messages": 0,
            "validation_errors": 0,
            "processing_times": [],
            "average_processing_time": 0.0
        }