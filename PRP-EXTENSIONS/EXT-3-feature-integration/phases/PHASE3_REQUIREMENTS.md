# Phase 3: WebSocket Message Enhancement & Real-time Integration

## Phase Overview
- **Phase Name**: WebSocket Message Enhancement & Real-time Integration
- **Phase Number**: 3 of 4
- **Estimated Duration**: 5-7 days
- **Implementation Effort**: 25% of total extension
- **Primary Focus**: Replace generic WebSocket messages with typed structures and implement reliable real-time data streaming

## Phase Objectives

### Primary Goals
1. **Implement Typed WebSocket Messages**: Replace `Dict[str, Any]` with specific message classes
2. **Add Message Validation**: Implement validation on both backend and frontend
3. **Enhance Connection Reliability**: Add automatic reconnection with exponential backoff
4. **Stream Real-time Analytics**: Integrate live analytics data with existing dashboard components
5. **Standardize Message Versioning**: Add versioning system for future compatibility

### Success Criteria
- [ ] WebSocket messages use typed structures instead of Dict[str, Any]
- [ ] Real-time analytics data streams reliably to frontend
- [ ] WebSocket connections automatically reconnect on failure
- [ ] Message processing and rendering completed within 50ms target  
- [ ] Connection status properly reported to users

## Prerequisites from Phase 2
- [x] Complete analytics dashboard with all 11 endpoints functional
- [x] Analytics data hooks available for real-time integration
- [x] Component architecture ready for WebSocket integration
- [x] Type-safe API client with field transformations working

## Technical Requirements

### Backend WebSocket Message System

#### 1. Typed Message Class Hierarchy
```python
# src/backend/websocket/message_types.py

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum

class MessageVersion(str, Enum):
    V1_0 = "1.0"
    CURRENT = V1_0

class WebSocketMessage(BaseModel, ABC):
    """Base class for all WebSocket messages with version support."""
    
    message_type: str = Field(..., description="Type identifier for message routing")
    version: MessageVersion = Field(default=MessageVersion.CURRENT, description="Message format version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message creation timestamp")
    
    @validator('timestamp')
    def serialize_timestamp(cls, v):
        if isinstance(v, datetime):
            return v.isoformat() + 'Z'
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }

# Market Data Messages
class MarketDataUpdate(BaseModel):
    """Market data update payload."""
    instrument_id: int
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    change_percent: Optional[float] = None

class MarketDataMessage(WebSocketMessage):
    """Real-time market data updates."""
    message_type: Literal["market_data"] = "market_data"
    data: MarketDataUpdate

# Alert Messages  
class AlertNotification(BaseModel):
    """Alert notification payload."""
    alert_id: int
    rule_id: int
    instrument_id: int
    symbol: str
    rule_name: str
    condition: str
    target_value: float
    current_value: float
    severity: Literal["low", "medium", "high"]
    message: str

class AlertMessage(WebSocketMessage):
    """Alert notifications."""
    message_type: Literal["alert"] = "alert"
    data: AlertNotification

# Analytics Messages
class AnalyticsUpdate(BaseModel):
    """Analytics update payload."""
    instrument_id: int
    symbol: str
    analysis_type: str
    results: Dict[str, Any]
    calculation_time: datetime
    next_update: Optional[datetime] = None

class AnalyticsMessage(WebSocketMessage):
    """Real-time analytics updates."""
    message_type: Literal["analytics_update"] = "analytics_update"
    data: AnalyticsUpdate

# Technical Indicator Messages
class TechnicalIndicatorUpdate(BaseModel):
    """Technical indicator update payload."""
    instrument_id: int
    symbol: str
    indicators: Dict[str, Any]  # RSI, MACD, etc.
    calculated_at: datetime

class TechnicalIndicatorMessage(WebSocketMessage):
    """Real-time technical indicator updates."""
    message_type: Literal["technical_indicators"] = "technical_indicators" 
    data: TechnicalIndicatorUpdate

# Connection Management Messages
class ConnectionStatus(BaseModel):
    """Connection status information."""
    client_id: str
    connected_at: datetime
    subscriptions: List[str]
    last_heartbeat: datetime

class ConnectionMessage(WebSocketMessage):
    """Connection status and heartbeat messages."""
    message_type: Literal["connection_status"] = "connection_status"
    data: ConnectionStatus

class ErrorDetails(BaseModel):
    """Error information payload."""
    error_code: str
    error_message: str
    request_id: Optional[str] = None
    timestamp: datetime

class ErrorMessage(WebSocketMessage):
    """Error notifications."""
    message_type: Literal["error"] = "error"
    data: ErrorDetails

# Message Type Union
IncomingMessage = Union[
    MarketDataMessage,
    AlertMessage, 
    AnalyticsMessage,
    TechnicalIndicatorMessage,
    ConnectionMessage,
    ErrorMessage
]
```

#### 2. Message Validation and Routing
```python
# src/backend/websocket/message_handler.py

import json
import structlog
from fastapi import WebSocket
from typing import Dict, Any, Optional
from .message_types import (
    WebSocketMessage, IncomingMessage, MessageVersion,
    MarketDataMessage, AlertMessage, AnalyticsMessage,
    ErrorMessage, ErrorDetails
)

logger = structlog.get_logger()

class MessageHandler:
    """Handles WebSocket message validation, routing, and processing."""
    
    def __init__(self):
        self.message_validators = {
            "market_data": MarketDataMessage,
            "alert": AlertMessage,
            "analytics_update": AnalyticsMessage,
            "technical_indicators": TechnicalIndicatorMessage,
            "connection_status": ConnectionMessage,
        }
    
    async def validate_message(self, message_data: Dict[str, Any]) -> Optional[WebSocketMessage]:
        """Validate incoming message against appropriate schema."""
        try:
            message_type = message_data.get("message_type")
            if not message_type:
                raise ValueError("Missing message_type field")
            
            validator_class = self.message_validators.get(message_type)
            if not validator_class:
                raise ValueError(f"Unknown message type: {message_type}")
            
            # Validate message structure
            validated_message = validator_class(**message_data)
            return validated_message
            
        except Exception as e:
            logger.error(f"Message validation failed: {e}", message_data=message_data)
            return None
    
    async def create_error_message(self, error_code: str, error_message: str, 
                                 request_id: Optional[str] = None) -> ErrorMessage:
        """Create standardized error message."""
        return ErrorMessage(
            data=ErrorDetails(
                error_code=error_code,
                error_message=error_message,
                request_id=request_id,
                timestamp=datetime.utcnow()
            )
        )
    
    async def serialize_message(self, message: WebSocketMessage) -> str:
        """Serialize message to JSON string."""
        try:
            return message.json()
        except Exception as e:
            logger.error(f"Message serialization failed: {e}")
            error_msg = await self.create_error_message(
                "SERIALIZATION_ERROR",
                f"Failed to serialize message: {str(e)}"
            )
            return error_msg.json()
```

#### 3. Enhanced WebSocket Connection Manager
```python
# src/backend/websocket/connection_manager.py

import asyncio
import json
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from .message_handler import MessageHandler
from .message_types import (
    WebSocketMessage, ConnectionMessage, ConnectionStatus,
    AnalyticsMessage, AnalyticsUpdate, TechnicalIndicatorMessage
)

logger = structlog.get_logger()

class ConnectionManager:
    """Enhanced connection manager with typed message support."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}
        self.message_handler = MessageHandler()
        self.heartbeat_interval = 30  # seconds
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept WebSocket connection with enhanced tracking."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        
        # Send connection confirmation
        connection_msg = ConnectionMessage(
            data=ConnectionStatus(
                client_id=client_id,
                connected_at=datetime.utcnow(),
                subscriptions=[],
                last_heartbeat=datetime.utcnow()
            )
        )
        
        await self.send_personal_message(connection_msg, client_id)
        logger.info(f"Client {client_id} connected")
        
        # Start heartbeat if first connection
        if len(self.active_connections) == 1 and not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    def disconnect(self, client_id: str):
        """Remove client connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        logger.info(f"Client {client_id} disconnected")
        
        # Stop heartbeat if no connections
        if not self.active_connections and self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
    
    async def send_personal_message(self, message: WebSocketMessage, client_id: str):
        """Send typed message to specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                message_json = await self.message_handler.serialize_message(message)
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_message(self, message: WebSocketMessage, 
                              subscription_filter: Optional[str] = None):
        """Broadcast typed message to all connected clients or filtered subset."""
        if not self.active_connections:
            return
        
        message_json = await self.message_handler.serialize_message(message)
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            # Apply subscription filter if specified
            if (subscription_filter and 
                subscription_filter not in self.client_subscriptions.get(client_id, set())):
                continue
            
            try:
                await websocket.send_text(message_json)
            except WebSocketDisconnect:
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def handle_client_message(self, websocket: WebSocket, client_id: str, 
                                  data: Dict[str, Any]):
        """Handle incoming client messages with validation."""
        validated_message = await self.message_handler.validate_message(data)
        
        if not validated_message:
            error_msg = await self.message_handler.create_error_message(
                "INVALID_MESSAGE",
                "Message validation failed",
                data.get("request_id")
            )
            await self.send_personal_message(error_msg, client_id)
            return
        
        # Handle subscription requests
        if validated_message.message_type == "subscribe":
            await self._handle_subscription(client_id, data)
        elif validated_message.message_type == "unsubscribe":
            await self._handle_unsubscription(client_id, data)
        else:
            logger.warning(f"Unhandled message type: {validated_message.message_type}")
    
    async def stream_analytics_update(self, instrument_id: int, analysis_type: str, 
                                    results: Dict[str, Any]):
        """Stream analytics update to subscribed clients."""
        analytics_msg = AnalyticsMessage(
            data=AnalyticsUpdate(
                instrument_id=instrument_id,
                symbol=results.get('symbol', ''),
                analysis_type=analysis_type,
                results=results,
                calculation_time=datetime.utcnow()
            )
        )
        
        await self.broadcast_message(analytics_msg, f"analytics_{instrument_id}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages."""
        while self.active_connections:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                heartbeat_msg = ConnectionMessage(
                    data=ConnectionStatus(
                        client_id="server",
                        connected_at=datetime.utcnow(),
                        subscriptions=[],
                        last_heartbeat=datetime.utcnow()
                    )
                )
                
                await self.broadcast_message(heartbeat_msg)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

# Global connection manager instance
websocket_manager = ConnectionManager()
```

### Frontend WebSocket Type System

#### 1. TypeScript Message Interfaces
```typescript
// src/frontend/src/types/websocket.ts

// Base message interface
interface WebSocketMessage {
  message_type: string;
  version: string;
  timestamp: string;
}

// Incoming message types
interface MarketDataUpdate {
  instrumentId: number;
  symbol: string;
  price: number;
  volume: number;
  timestamp: string;
  changePercent?: number;
}

interface MarketDataMessage extends WebSocketMessage {
  message_type: 'market_data';
  data: MarketDataUpdate;
}

interface AlertNotification {
  alertId: number;
  ruleId: number;
  instrumentId: number;
  symbol: string;
  ruleName: string;
  condition: string;
  targetValue: number;
  currentValue: number;
  severity: 'low' | 'medium' | 'high';
  message: string;
}

interface AlertMessage extends WebSocketMessage {
  message_type: 'alert';
  data: AlertNotification;
}

interface AnalyticsUpdate {
  instrumentId: number;
  symbol: string;
  analysisType: string;
  results: Record<string, any>;
  calculationTime: string;
  nextUpdate?: string;
}

interface AnalyticsMessage extends WebSocketMessage {
  message_type: 'analytics_update';
  data: AnalyticsUpdate;
}

interface TechnicalIndicatorUpdate {
  instrumentId: number;
  symbol: string;
  indicators: Record<string, any>;
  calculatedAt: string;
}

interface TechnicalIndicatorMessage extends WebSocketMessage {
  message_type: 'technical_indicators';
  data: TechnicalIndicatorUpdate;
}

interface ConnectionStatus {
  clientId: string;
  connectedAt: string;
  subscriptions: string[];
  lastHeartbeat: string;
}

interface ConnectionMessage extends WebSocketMessage {
  message_type: 'connection_status';
  data: ConnectionStatus;
}

interface ErrorDetails {
  errorCode: string;
  errorMessage: string;
  requestId?: string;
  timestamp: string;
}

interface ErrorMessage extends WebSocketMessage {
  message_type: 'error';
  data: ErrorDetails;
}

// Union type for all incoming messages
export type IncomingMessage = 
  | MarketDataMessage
  | AlertMessage
  | AnalyticsMessage
  | TechnicalIndicatorMessage
  | ConnectionMessage
  | ErrorMessage;

// Outgoing message types
interface SubscriptionRequest {
  message_type: 'subscribe';
  subscription_type: string;
  instrument_id?: number;
  request_id?: string;
}

interface UnsubscriptionRequest {
  message_type: 'unsubscribe';
  subscription_type: string;
  instrument_id?: number;
  request_id?: string;
}

export type OutgoingMessage = SubscriptionRequest | UnsubscriptionRequest;
```

#### 2. Enhanced WebSocket Context
```typescript
// src/frontend/src/context/WebSocketContext.tsx

import React, { createContext, useContext, useEffect, useReducer, useCallback } from 'react';
import { snakeToCamel } from '../utils/typeTransforms';
import { IncomingMessage, OutgoingMessage } from '../types/websocket';

interface WebSocketState {
  socket: WebSocket | null;
  isConnected: boolean;
  lastMessage: IncomingMessage | null;
  error: string | null;
  reconnectCount: number;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
}

type WebSocketAction =
  | { type: 'CONNECTING' }
  | { type: 'CONNECTED'; payload: WebSocket }
  | { type: 'DISCONNECTED' }
  | { type: 'ERROR'; payload: string }
  | { type: 'MESSAGE_RECEIVED'; payload: IncomingMessage }
  | { type: 'RECONNECT_ATTEMPT'; payload: number };

const initialState: WebSocketState = {
  socket: null,
  isConnected: false,
  lastMessage: null,
  error: null,
  reconnectCount: 0,
  connectionStatus: 'disconnected',
};

function websocketReducer(state: WebSocketState, action: WebSocketAction): WebSocketState {
  switch (action.type) {
    case 'CONNECTING':
      return {
        ...state,
        connectionStatus: 'connecting',
        error: null,
      };
    case 'CONNECTED':
      return {
        ...state,
        socket: action.payload,
        isConnected: true,
        connectionStatus: 'connected',
        error: null,
        reconnectCount: 0,
      };
    case 'DISCONNECTED':
      return {
        ...state,
        socket: null,
        isConnected: false,
        connectionStatus: 'disconnected',
        lastMessage: null,
      };
    case 'ERROR':
      return {
        ...state,
        error: action.payload,
        connectionStatus: 'error',
        isConnected: false,
      };
    case 'MESSAGE_RECEIVED':
      return {
        ...state,
        lastMessage: action.payload,
        error: null,
      };
    case 'RECONNECT_ATTEMPT':
      return {
        ...state,
        reconnectCount: action.payload,
      };
    default:
      return state;
  }
}

interface WebSocketContextValue extends WebSocketState {
  sendMessage: (message: OutgoingMessage) => void;
  subscribe: (subscriptionType: string, instrumentId?: number) => void;
  unsubscribe: (subscriptionType: string, instrumentId?: number) => void;
  reconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(websocketReducer, initialState);
  
  const connect = useCallback(() => {
    if (state.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    dispatch({ type: 'CONNECTING' });

    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/realtime';
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('WebSocket connected');
      dispatch({ type: 'CONNECTED', payload: socket });
    };

    socket.onmessage = (event) => {
      try {
        const rawMessage = JSON.parse(event.data);
        
        // Transform snake_case to camelCase
        const transformedMessage = snakeToCamel(rawMessage) as IncomingMessage;
        
        // Validate message structure
        if (isValidMessage(transformedMessage)) {
          dispatch({ type: 'MESSAGE_RECEIVED', payload: transformedMessage });
        } else {
          console.warn('Received invalid message:', transformedMessage);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        dispatch({ type: 'ERROR', payload: 'Failed to parse message' });
      }
    };

    socket.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      dispatch({ type: 'DISCONNECTED' });
      
      // Implement exponential backoff reconnection
      if (!event.wasClean) {
        const delay = Math.min(1000 * Math.pow(2, state.reconnectCount), 30000);
        setTimeout(() => {
          dispatch({ type: 'RECONNECT_ATTEMPT', payload: state.reconnectCount + 1 });
          connect();
        }, delay);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      dispatch({ type: 'ERROR', payload: 'Connection error' });
    };
  }, [state.reconnectCount]);

  const sendMessage = useCallback((message: OutgoingMessage) => {
    if (state.socket?.readyState === WebSocket.OPEN) {
      state.socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, [state.socket]);

  const subscribe = useCallback((subscriptionType: string, instrumentId?: number) => {
    sendMessage({
      message_type: 'subscribe',
      subscription_type: subscriptionType,
      instrument_id: instrumentId,
      request_id: `sub_${Date.now()}_${Math.random()}`,
    });
  }, [sendMessage]);

  const unsubscribe = useCallback((subscriptionType: string, instrumentId?: number) => {
    sendMessage({
      message_type: 'unsubscribe',
      subscription_type: subscriptionType,
      instrument_id: instrumentId,
      request_id: `unsub_${Date.now()}_${Math.random()}`,
    });
  }, [sendMessage]);

  const reconnect = useCallback(() => {
    if (state.socket) {
      state.socket.close();
    }
    connect();
  }, [connect, state.socket]);

  useEffect(() => {
    connect();
    
    return () => {
      if (state.socket) {
        state.socket.close();
      }
    };
  }, []);

  const contextValue: WebSocketContextValue = {
    ...state,
    sendMessage,
    subscribe,
    unsubscribe,
    reconnect,
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = (): WebSocketContextValue => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

// Message validation helper
function isValidMessage(message: any): message is IncomingMessage {
  return (
    typeof message === 'object' &&
    message !== null &&
    typeof message.message_type === 'string' &&
    typeof message.timestamp === 'string' &&
    message.data !== undefined
  );
}
```

#### 3. Real-time Analytics Integration Hook
```typescript
// src/frontend/src/hooks/useRealTimeAnalytics.ts

import { useEffect, useState, useCallback } from 'react';
import { useWebSocket } from '../context/WebSocketContext';
import { AnalyticsMessage, TechnicalIndicatorMessage } from '../types/websocket';

interface RealTimeAnalyticsData {
  marketAnalysis: Record<number, any>;
  technicalIndicators: Record<number, any>;
  lastUpdated: Record<number, string>;
}

export const useRealTimeAnalytics = (instrumentIds: number[] = []) => {
  const { lastMessage, isConnected, subscribe, unsubscribe } = useWebSocket();
  const [analyticsData, setAnalyticsData] = useState<RealTimeAnalyticsData>({
    marketAnalysis: {},
    technicalIndicators: {},
    lastUpdated: {},
  });

  // Subscribe to analytics updates for specified instruments
  useEffect(() => {
    if (isConnected && instrumentIds.length > 0) {
      instrumentIds.forEach(instrumentId => {
        subscribe('analytics', instrumentId);
        subscribe('technical_indicators', instrumentId);
      });

      return () => {
        instrumentIds.forEach(instrumentId => {
          unsubscribe('analytics', instrumentId);
          unsubscribe('technical_indicators', instrumentId);
        });
      };
    }
  }, [isConnected, instrumentIds, subscribe, unsubscribe]);

  // Handle incoming analytics messages
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.message_type === 'analytics_update') {
      const message = lastMessage as AnalyticsMessage;
      setAnalyticsData(prev => ({
        ...prev,
        marketAnalysis: {
          ...prev.marketAnalysis,
          [message.data.instrumentId]: message.data.results,
        },
        lastUpdated: {
          ...prev.lastUpdated,
          [message.data.instrumentId]: message.data.calculationTime,
        },
      }));
    } else if (lastMessage.message_type === 'technical_indicators') {
      const message = lastMessage as TechnicalIndicatorMessage;
      setAnalyticsData(prev => ({
        ...prev,
        technicalIndicators: {
          ...prev.technicalIndicators,
          [message.data.instrumentId]: message.data.indicators,
        },
        lastUpdated: {
          ...prev.lastUpdated,
          [message.data.instrumentId]: message.data.calculatedAt,
        },
      }));
    }
  }, [lastMessage]);

  const getAnalyticsForInstrument = useCallback((instrumentId: number) => {
    return {
      marketAnalysis: analyticsData.marketAnalysis[instrumentId] || null,
      technicalIndicators: analyticsData.technicalIndicators[instrumentId] || null,
      lastUpdated: analyticsData.lastUpdated[instrumentId] || null,
    };
  }, [analyticsData]);

  return {
    analyticsData,
    getAnalyticsForInstrument,
    isConnected,
  };
};
```

## Implementation Tasks

### Task 1: Backend Message System (Days 1-2)
1. **Create Typed Message Classes**
   - Implement complete message hierarchy with Pydantic validation
   - Add message versioning system for future compatibility
   - Create validation utilities for message processing

2. **Enhance Connection Manager**
   - Update connection manager with typed message support
   - Implement message validation and error handling
   - Add heartbeat mechanism and connection status tracking

### Task 2: Frontend Type System (Days 3-4)
1. **Create TypeScript Interfaces**
   - Implement all WebSocket message interfaces
   - Add message validation utilities
   - Create type guards for message discrimination

2. **Enhance WebSocket Context**
   - Update context with typed message handling
   - Implement automatic reconnection with exponential backoff
   - Add subscription management for specific data types

### Task 3: Real-time Integration (Days 5-6)
1. **Analytics Components Integration**
   - Update analytics components to use real-time data
   - Implement live indicator updates in dashboard
   - Add real-time market analysis streaming

2. **Performance Optimization**
   - Implement efficient message processing (target <50ms)
   - Add message queuing for high-frequency updates
   - Optimize component rendering for real-time data

### Task 4: Testing & Validation (Day 7)
1. **Message Validation Testing**
   - Test message serialization/deserialization
   - Validate message routing and handling
   - Test connection reliability and reconnection

2. **Real-time Performance Testing**
   - Measure message processing latency
   - Test WebSocket connection stability
   - Validate analytics dashboard performance with live data

## Phase 3 Dependencies

### Requires from Phase 2
- [x] Complete analytics dashboard functional
- [x] Analytics components ready for real-time data
- [x] Type-safe API client with transformations

### Provides to Phase 4
- Reliable WebSocket infrastructure for authenticated streaming
- Real-time analytics data streaming to dashboard
- Typed message system ready for authenticated channels

## Testing Requirements

### Backend Tests
```python
def test_message_validation():
    # Test typed message creation and validation
    message_data = {
        "message_type": "analytics_update",
        "data": {
            "instrument_id": 1,
            "symbol": "AAPL",
            "analysis_type": "market_analysis",
            "results": {"trend": "bullish"},
            "calculation_time": datetime.utcnow()
        }
    }
    
    handler = MessageHandler()
    validated_message = await handler.validate_message(message_data)
    
    assert isinstance(validated_message, AnalyticsMessage)
    assert validated_message.data.instrument_id == 1

def test_websocket_broadcasting():
    # Test message broadcasting to connected clients
    manager = ConnectionManager()
    # Mock connections and test broadcasting
```

### Frontend Tests
```typescript
describe('WebSocket Message Handling', () => {
  test('processes analytics messages correctly', () => {
    const mockMessage = {
      message_type: 'analytics_update',
      data: {
        instrumentId: 1,
        analysisType: 'market_analysis',
        results: { trend: 'bullish' }
      }
    };
    
    // Test message processing
    expect(isValidMessage(mockMessage)).toBe(true);
  });

  test('handles connection failures with reconnection', async () => {
    // Test automatic reconnection logic
  });
});
```

## Phase 3 Completion Criteria

### Functional Completion
- [ ] All WebSocket messages use typed structures instead of generic Dict[str, Any]
- [ ] Message validation working on both backend and frontend
- [ ] WebSocket connections automatically reconnect on failure with exponential backoff
- [ ] Real-time analytics data streams to dashboard components
- [ ] Connection status properly reported to users

### Technical Validation
- [ ] Message processing completes within 50ms target performance
- [ ] WebSocket connection stability demonstrated under load
- [ ] Message versioning system functional for future compatibility
- [ ] All message types properly validated and routed

### Integration Readiness
- [ ] WebSocket infrastructure ready for authenticated streaming in Phase 4
- [ ] Real-time data integration seamless with existing analytics components
- [ ] Message system scalable for additional real-time features

**Phase 3 Success Metric**: Reliable real-time data streaming with <50ms latency + Complete message type safety + Connection reliability >99.9% + Foundation ready for authenticated real-time features