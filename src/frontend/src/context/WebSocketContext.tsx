/**
 * WebSocket Context Provider
 * 
 * Provides real-time WebSocket connection management with automatic reconnection,
 * message handling, and state management for the entire application.
 */

import React, { createContext, useContext, useEffect, useReducer, useCallback, useRef } from 'react';
import { 
  WebSocketIncomingMessage, 
  WebSocketState, 
  TickUpdateMessage, 
  AlertFiredMessage, 
  HealthStatusMessage,
  MarketData,
  AlertLogWithDetails,
  HealthStatus,
  AlertStatus,
  DeliveryStatus
} from '../types';

// =============================================================================
// STATE MANAGEMENT
// =============================================================================

interface WebSocketContextState extends WebSocketState {
  realtimeData: Record<number, MarketData>;
  recentAlerts: AlertLogWithDetails[];
  systemHealth: HealthStatus | null;
}

type WebSocketAction = 
  | { type: 'CONNECT' }
  | { type: 'DISCONNECT' }
  | { type: 'RECONNECTING' }
  | { type: 'ERROR'; payload: string }
  | { type: 'TICK_UPDATE'; payload: TickUpdateMessage['data'] }
  | { type: 'ALERT_FIRED'; payload: AlertFiredMessage['data'] }
  | { type: 'HEALTH_STATUS'; payload: HealthStatus }
  | { type: 'RESET_RECONNECT_ATTEMPTS' };

const initialState: WebSocketContextState = {
  isConnected: false,
  reconnectAttempts: 0,
  realtimeData: {},
  recentAlerts: [],
  systemHealth: null,
  error: null
};

function websocketReducer(state: WebSocketContextState, action: WebSocketAction): WebSocketContextState {
  switch (action.type) {
    case 'CONNECT':
      return {
        ...state,
        isConnected: true,
        error: null,
        reconnectAttempts: 0
      };
    
    case 'DISCONNECT':
      return {
        ...state,
        isConnected: false
      };
    
    case 'RECONNECTING':
      return {
        ...state,
        isConnected: false,
        reconnectAttempts: state.reconnectAttempts + 1
      };
    
    case 'ERROR':
      return {
        ...state,
        isConnected: false,
        error: action.payload
      };
    
    case 'TICK_UPDATE':
      const tickData = action.payload;
      const marketData: MarketData = {
        id: Date.now(), // Temporary ID for real-time data
        timestamp: tickData.timestamp,
        instrument_id: tickData.instrument_id,
        price: tickData.price,
        volume: tickData.volume || null,
        bid: tickData.bid || null,
        ask: tickData.ask || null,
        bid_size: null,
        ask_size: null,
        open_price: null,
        high_price: null,
        low_price: null
      };
      
      return {
        ...state,
        realtimeData: {
          ...state.realtimeData,
          [tickData.instrument_id]: marketData
        }
      };
    
    case 'ALERT_FIRED':
      const alertData = action.payload;
      const newAlert: AlertLogWithDetails = {
        id: alertData.alert_id,
        timestamp: new Date().toISOString(),
        rule_id: alertData.rule_id,
        instrument_id: alertData.instrument_id,
        trigger_value: alertData.trigger_value,
        threshold_value: alertData.threshold_value,
        fired_status: 'fired' as AlertStatus,
        delivery_status: 'pending' as DeliveryStatus,
        rule_condition: alertData.rule_condition,
        alert_message: alertData.message,
        evaluation_time_ms: null,
        error_message: null,
        delivery_attempted_at: null,
        delivery_completed_at: null
      };
      
      return {
        ...state,
        recentAlerts: [newAlert, ...state.recentAlerts.slice(0, 49)] // Keep last 50 alerts
      };
    
    case 'HEALTH_STATUS':
      return {
        ...state,
        systemHealth: action.payload
      };
    
    case 'RESET_RECONNECT_ATTEMPTS':
      return {
        ...state,
        reconnectAttempts: 0
      };
    
    default:
      return state;
  }
}

// =============================================================================
// CONTEXT DEFINITION
// =============================================================================

interface WebSocketContextValue extends WebSocketContextState {
  connect: () => void;
  disconnect: () => void;
  sendMessage: (message: object) => void;
}

export const WebSocketContext = createContext<WebSocketContextValue | null>(null);

// =============================================================================
// PROVIDER COMPONENT
// =============================================================================

interface WebSocketProviderProps {
  children: React.ReactNode;
  wsUrl?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/realtime',
  reconnectInterval = 3000,
  maxReconnectAttempts = 10
}) => {
  const [state, dispatch] = useReducer(websocketReducer, initialState);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // =============================================================================
  // WebSocket MESSAGE HANDLING
  // =============================================================================
  
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketIncomingMessage = JSON.parse(event.data);
      
      switch (message.type) {
        case 'tick_update':
          dispatch({ type: 'TICK_UPDATE', payload: message.data });
          break;
        
        case 'alert_fired':
          dispatch({ type: 'ALERT_FIRED', payload: message.data });
          break;
        
        case 'health_status':
          dispatch({ type: 'HEALTH_STATUS', payload: message.data });
          break;
        
        case 'pong':
          // Handle pong response (connection alive)
          break;
        
        default:
          console.warn('Unknown WebSocket message type:', message);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, []);

  // =============================================================================
  // CONNECTION MANAGEMENT
  // =============================================================================
  
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.CONNECTING || 
        wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        dispatch({ type: 'CONNECT' });
        
        // Start ping interval for connection health
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }));
          }
        }, 30000); // Ping every 30 seconds
      };

      ws.onmessage = handleMessage;

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        dispatch({ type: 'DISCONNECT' });
        
        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Attempt reconnection if not intentional disconnect
        if (event.code !== 1000 && state.reconnectAttempts < maxReconnectAttempts) {
          const delay = Math.min(reconnectInterval * Math.pow(2, state.reconnectAttempts), 30000);
          console.log(`Reconnecting in ${delay}ms (attempt ${state.reconnectAttempts + 1})`);
          
          dispatch({ type: 'RECONNECTING' });
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        dispatch({ type: 'ERROR', payload: 'WebSocket connection error' });
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      dispatch({ type: 'ERROR', payload: 'Failed to create WebSocket connection' });
    }
  }, [wsUrl, handleMessage, state.reconnectAttempts, maxReconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Intentional disconnect');
      wsRef.current = null;
    }
    
    dispatch({ type: 'RESET_RECONNECT_ATTEMPTS' });
  }, []);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }, []);

  // =============================================================================
  // LIFECYCLE MANAGEMENT
  // =============================================================================
  
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, []); // Only run on mount/unmount

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // =============================================================================
  // CONTEXT VALUE
  // =============================================================================
  
  const contextValue: WebSocketContextValue = {
    ...state,
    connect,
    disconnect,
    sendMessage
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};

// =============================================================================
// CUSTOM HOOK
// =============================================================================

export const useWebSocket = (): WebSocketContextValue => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};