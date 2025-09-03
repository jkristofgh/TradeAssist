/**
 * WebSocket Context Provider
 * 
 * Provides real-time WebSocket connection management with automatic reconnection,
 * message handling, and state management for the entire application.
 */

import React, { createContext, useContext, useEffect, useReducer, useCallback, useRef } from 'react';
import { 
  IncomingMessage, 
  OutgoingMessage,
  WebSocketPerformanceMetrics,
  WebSocketSubscriptions,
  SubscriptionState,
  isValidIncomingMessage,
  isMarketDataMessage,
  isAnalyticsMessage,
  isTechnicalIndicatorMessage,
  isAlertMessage,
  isPricePredictionMessage,
  isRiskMetricsMessage,
  isConnectionMessage,
  isErrorMessage,
  isPongMessage,
  createPingMessage,
  createSubscriptionMessage,
  createUnsubscriptionMessage,
  MarketDataUpdate,
  AnalyticsUpdate,
  TechnicalIndicatorUpdate,
  AlertNotification,
  PricePredictionUpdate,
  RiskMetricsUpdate
} from '../types/websocket';
import { 
  WebSocketState, 
  MarketData,
  AlertLogWithDetails,
  HealthStatus,
  AlertStatus,
  DeliveryStatus
} from '../types';
import { snakeToCamel } from '../utils/typeTransforms';

// =============================================================================
// STATE MANAGEMENT
// =============================================================================

interface WebSocketContextState extends WebSocketState {
  realtimeData: Record<number, MarketData>;
  recentAlerts: AlertLogWithDetails[];
  systemHealth: HealthStatus | null;
  analyticsData: Record<number, AnalyticsUpdate>;
  technicalIndicators: Record<number, TechnicalIndicatorUpdate>;
  pricePredictions: Record<number, PricePredictionUpdate>;
  riskMetrics: Record<number, RiskMetricsUpdate>;
  subscriptions: WebSocketSubscriptions;
  performanceMetrics: WebSocketPerformanceMetrics;
  clientId?: string;
}

type WebSocketAction = 
  | { type: 'CONNECT'; payload: { clientId: string } }
  | { type: 'DISCONNECT' }
  | { type: 'RECONNECTING' }
  | { type: 'ERROR'; payload: string }
  | { type: 'MESSAGE_RECEIVED'; payload: { message: IncomingMessage; processingTime: number } }
  | { type: 'SUBSCRIPTION_UPDATED'; payload: { subscriptionType: string; status: SubscriptionState['status']; error?: string } }
  | { type: 'RESET_RECONNECT_ATTEMPTS' };

const initialState: WebSocketContextState = {
  isConnected: false,
  reconnectAttempts: 0,
  realtimeData: {},
  recentAlerts: [],
  systemHealth: null,
  analyticsData: {},
  technicalIndicators: {},
  pricePredictions: {},
  riskMetrics: {},
  subscriptions: {},
  performanceMetrics: {
    messagesReceived: 0,
    averageProcessingTime: 0,
    errorRate: 0,
    connectionQuality: 'disconnected'
  },
  error: null
};

function websocketReducer(state: WebSocketContextState, action: WebSocketAction): WebSocketContextState {
  switch (action.type) {
    case 'CONNECT':
      return {
        ...state,
        isConnected: true,
        error: null,
        reconnectAttempts: 0,
        clientId: action.payload.clientId,
        performanceMetrics: {
          ...state.performanceMetrics,
          connectionQuality: 'good'
        }
      };
    
    case 'DISCONNECT':
      return {
        ...state,
        isConnected: false,
        performanceMetrics: {
          ...state.performanceMetrics,
          connectionQuality: 'disconnected'
        }
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
        error: action.payload,
        performanceMetrics: {
          ...state.performanceMetrics,
          connectionQuality: 'poor',
          errorRate: state.performanceMetrics.errorRate + 1
        }
      };
    
    case 'MESSAGE_RECEIVED':
      const { message, processingTime } = action.payload;
      const newState = { ...state };
      
      // Update performance metrics
      const totalMessages = newState.performanceMetrics.messagesReceived + 1;
      const avgProcessingTime = ((newState.performanceMetrics.averageProcessingTime * newState.performanceMetrics.messagesReceived) + processingTime) / totalMessages;
      
      newState.performanceMetrics = {
        ...newState.performanceMetrics,
        messagesReceived: totalMessages,
        averageProcessingTime: avgProcessingTime,
        lastMessageTimestamp: message.timestamp,
        connectionQuality: avgProcessingTime < 50 ? 'excellent' : avgProcessingTime < 100 ? 'good' : 'poor'
      };
      
      // Route message to appropriate state
      if (isMarketDataMessage(message)) {
        console.log('📊 Market data message received:', message.data);
        const tickData = message.data;
        const marketData: MarketData = {
          id: Date.now(),
          timestamp: tickData.timestamp,
          instrumentId: tickData.instrumentId,
          price: tickData.price,
          volume: tickData.volume || null,
          bid: tickData.bid || null,
          ask: tickData.ask || null,
          bidSize: tickData.bidSize || null,
          askSize: tickData.askSize || null,
          openPrice: tickData.openPrice || null,
          highPrice: tickData.highPrice || null,
          lowPrice: tickData.lowPrice || null
        };
        newState.realtimeData = {
          ...newState.realtimeData,
          [tickData.instrumentId]: marketData
        };
        console.log('✅ Updated real-time data for instrument', tickData.instrumentId, 'price:', tickData.price);
      }
      
      else if (isAnalyticsMessage(message)) {
        newState.analyticsData = {
          ...newState.analyticsData,
          [message.data.instrumentId]: message.data
        };
      }
      
      else if (isTechnicalIndicatorMessage(message)) {
        newState.technicalIndicators = {
          ...newState.technicalIndicators,
          [message.data.instrumentId]: message.data
        };
      }
      
      else if (isPricePredictionMessage(message)) {
        newState.pricePredictions = {
          ...newState.pricePredictions,
          [message.data.instrumentId]: message.data
        };
      }
      
      else if (isRiskMetricsMessage(message)) {
        newState.riskMetrics = {
          ...newState.riskMetrics,
          [message.data.instrumentId]: message.data
        };
      }
      
      else if (isAlertMessage(message)) {
        const alertData = message.data;
        const newAlert: AlertLogWithDetails = {
          id: alertData.alertId,
          timestamp: message.timestamp,
          ruleId: alertData.ruleId,
          instrumentId: alertData.instrumentId,
          triggerValue: alertData.currentValue,
          thresholdValue: alertData.targetValue,
          firedStatus: 'fired' as AlertStatus,
          deliveryStatus: 'pending' as DeliveryStatus,
          ruleCondition: alertData.ruleCondition as any,
          alertMessage: alertData.message,
          evaluationTimeMs: alertData.evaluationTimeMs || null,
          errorMessage: null,
          deliveryAttemptedAt: null,
          deliveryCompletedAt: null
        };
        newState.recentAlerts = [newAlert, ...newState.recentAlerts.slice(0, 49)];
      }
      
      else if (isConnectionMessage(message)) {
        // Update connection status and extract client ID
        if (message.data.clientId) {
          console.log('🔗 Connection message received:', message.data);
          // Dispatch a separate CONNECT action to properly update state
          return {
            ...newState,
            isConnected: true,
            error: null,
            reconnectAttempts: 0,
            clientId: message.data.clientId,
            performanceMetrics: {
              ...newState.performanceMetrics,
              connectionQuality: 'good'
            }
          };
        }
      }
      
      return newState;
    
    case 'SUBSCRIPTION_UPDATED':
      const { subscriptionType, status, error } = action.payload;
      return {
        ...state,
        subscriptions: {
          ...state.subscriptions,
          [subscriptionType]: {
            subscriptionType,
            status,
            lastUpdate: new Date().toISOString(),
            errorMessage: error
          }
        }
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
  sendMessage: (message: OutgoingMessage) => void;
  subscribe: (subscriptionType: string, instrumentId?: number, parameters?: Record<string, any>) => void;
  unsubscribe: (subscriptionType: string, instrumentId?: number) => void;
  ping: () => void;
  getAnalyticsForInstrument: (instrumentId: number) => AnalyticsUpdate | null;
  getTechnicalIndicatorsForInstrument: (instrumentId: number) => TechnicalIndicatorUpdate | null;
  getPricePredictionForInstrument: (instrumentId: number) => PricePredictionUpdate | null;
  getRiskMetricsForInstrument: (instrumentId: number) => RiskMetricsUpdate | null;
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
  // ENHANCED MESSAGE HANDLING WITH PERFORMANCE TRACKING
  // =============================================================================
  
  const handleMessage = useCallback((event: MessageEvent) => {
    const startTime = performance.now();
    
    try {
      // Parse raw message
      const rawMessage = JSON.parse(event.data);
      
      // Transform snake_case to camelCase if needed
      const transformedMessage = snakeToCamel(rawMessage);
      
      // Validate message structure
      if (!isValidIncomingMessage(transformedMessage)) {
        console.warn('Received invalid message structure:', transformedMessage);
        dispatch({ type: 'ERROR', payload: 'Invalid message format' });
        return;
      }
      
      const processingTime = performance.now() - startTime;
      
      // Dispatch message with performance tracking
      dispatch({ 
        type: 'MESSAGE_RECEIVED', 
        payload: { 
          message: transformedMessage, 
          processingTime 
        } 
      });
      
      // Log slow message processing
      if (processingTime > 50) {
        console.warn(`Slow message processing: ${processingTime.toFixed(2)}ms for ${transformedMessage.messageType}`);
      }
      
    } catch (error) {
      console.error('Failed to parse or process WebSocket message:', error);
      dispatch({ type: 'ERROR', payload: 'Message processing error' });
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
        
        // Start ping interval for connection health
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            const pingMessage = createPingMessage(Date.now());
            ws.send(JSON.stringify(pingMessage));
          } else {
            // Clear ping interval if connection is not open
            if (pingIntervalRef.current) {
              clearInterval(pingIntervalRef.current);
              pingIntervalRef.current = null;
            }
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
        } else if (state.reconnectAttempts >= maxReconnectAttempts) {
          console.error('Max reconnection attempts reached');
          dispatch({ type: 'ERROR', payload: 'Max reconnection attempts reached' });
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
  }, [wsUrl, handleMessage, maxReconnectAttempts, reconnectInterval]); // Removed state.reconnectAttempts dependency

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

  const sendMessage = useCallback((message: OutgoingMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        dispatch({ type: 'ERROR', payload: 'Failed to send message' });
      }
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }, []);
  
  const subscribe = useCallback((subscriptionType: string, instrumentId?: number, parameters?: Record<string, any>) => {
    const subscriptionMessage = createSubscriptionMessage(subscriptionType, instrumentId, parameters);
    sendMessage(subscriptionMessage);
    
    // Update subscription state
    dispatch({ 
      type: 'SUBSCRIPTION_UPDATED', 
      payload: { 
        subscriptionType: instrumentId ? `${subscriptionType}_${instrumentId}` : subscriptionType, 
        status: 'subscribing' 
      } 
    });
  }, [sendMessage]);
  
  const unsubscribe = useCallback((subscriptionType: string, instrumentId?: number) => {
    const unsubscriptionMessage = createUnsubscriptionMessage(subscriptionType, instrumentId);
    sendMessage(unsubscriptionMessage);
    
    // Update subscription state
    dispatch({ 
      type: 'SUBSCRIPTION_UPDATED', 
      payload: { 
        subscriptionType: instrumentId ? `${subscriptionType}_${instrumentId}` : subscriptionType, 
        status: 'unsubscribing' 
      } 
    });
  }, [sendMessage]);
  
  const ping = useCallback(() => {
    const pingMessage = createPingMessage(Date.now());
    sendMessage(pingMessage);
  }, [sendMessage]);
  
  // Utility functions for accessing typed data
  const getAnalyticsForInstrument = useCallback((instrumentId: number): AnalyticsUpdate | null => {
    return state.analyticsData[instrumentId] || null;
  }, [state.analyticsData]);
  
  const getTechnicalIndicatorsForInstrument = useCallback((instrumentId: number): TechnicalIndicatorUpdate | null => {
    return state.technicalIndicators[instrumentId] || null;
  }, [state.technicalIndicators]);
  
  const getPricePredictionForInstrument = useCallback((instrumentId: number): PricePredictionUpdate | null => {
    return state.pricePredictions[instrumentId] || null;
  }, [state.pricePredictions]);
  
  const getRiskMetricsForInstrument = useCallback((instrumentId: number): RiskMetricsUpdate | null => {
    return state.riskMetrics[instrumentId] || null;
  }, [state.riskMetrics]);

  // =============================================================================
  // LIFECYCLE MANAGEMENT
  // =============================================================================
  
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, []); // Only run on mount/unmount

  // Auto-retry logic for connection failures
  useEffect(() => {
    if (state.error && !state.isConnected && state.reconnectAttempts < maxReconnectAttempts) {
      const retryDelay = Math.min(reconnectInterval * Math.pow(2, state.reconnectAttempts), 30000);
      
      console.log(`Auto-retrying connection in ${retryDelay}ms (attempt ${state.reconnectAttempts + 1})`);
      
      const retryTimeout = setTimeout(() => {
        dispatch({ type: 'RECONNECTING' });
        connect();
      }, retryDelay);
      
      return () => clearTimeout(retryTimeout);
    }
  }, [state.error, state.isConnected, state.reconnectAttempts, maxReconnectAttempts, reconnectInterval, connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // =============================================================================
  // CONTEXT VALUE
  // =============================================================================
  
  // Connection establishment logic is now handled in the message reducer
  // when connection_status messages are received
  
  const contextValue: WebSocketContextValue = {
    ...state,
    connect,
    disconnect,
    sendMessage,
    subscribe,
    unsubscribe,
    ping,
    getAnalyticsForInstrument,
    getTechnicalIndicatorsForInstrument,
    getPricePredictionForInstrument,
    getRiskMetricsForInstrument
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