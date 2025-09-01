/**
 * Enhanced WebSocket Type Definitions
 * 
 * Comprehensive TypeScript interfaces matching backend Pydantic models
 * for type-safe WebSocket communication with field transformations.
 */

// =============================================================================
// BASE MESSAGE INTERFACES
// =============================================================================

interface WebSocketMessage {
  messageType: string;
  version: string;
  timestamp: string;
}

// =============================================================================
// MARKET DATA MESSAGES
// =============================================================================

interface MarketDataUpdate {
  instrumentId: number;
  symbol: string;
  price: number;
  volume: number;
  timestamp: string;
  changePercent?: number;
  bid?: number;
  ask?: number;
  bidSize?: number;
  askSize?: number;
  openPrice?: number;
  highPrice?: number;
  lowPrice?: number;
}

interface MarketDataMessage extends WebSocketMessage {
  messageType: 'market_data';
  data: MarketDataUpdate;
}

// =============================================================================
// ALERT MESSAGES
// =============================================================================

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
  evaluationTimeMs?: number;
  ruleCondition: string;
}

interface AlertMessage extends WebSocketMessage {
  messageType: 'alert';
  data: AlertNotification;
}

// =============================================================================
// ANALYTICS MESSAGES
// =============================================================================

interface AnalyticsUpdate {
  instrumentId: number;
  symbol: string;
  analysisType: string;
  results: Record<string, any>;
  calculationTime: string;
  nextUpdate?: string;
  confidenceScore?: number;
  dataQualityScore?: number;
}

interface AnalyticsMessage extends WebSocketMessage {
  messageType: 'analytics_update';
  data: AnalyticsUpdate;
}

// =============================================================================
// TECHNICAL INDICATOR MESSAGES
// =============================================================================

interface TechnicalIndicatorUpdate {
  instrumentId: number;
  symbol: string;
  indicators: Record<string, any>;
  calculatedAt: string;
  timeframe: string;
  indicatorQuality?: Record<string, number>;
}

interface TechnicalIndicatorMessage extends WebSocketMessage {
  messageType: 'technical_indicators';
  data: TechnicalIndicatorUpdate;
}

// =============================================================================
// PRICE PREDICTION MESSAGES
// =============================================================================

interface PricePredictionUpdate {
  instrumentId: number;
  symbol: string;
  predictedPrice: number;
  confidenceInterval: Record<string, number>;
  predictionHorizonMinutes: number;
  modelName: string;
  predictionAccuracy?: number;
  calculatedAt: string;
}

interface PricePredictionMessage extends WebSocketMessage {
  messageType: 'price_prediction';
  data: PricePredictionUpdate;
}

// =============================================================================
// RISK METRICS MESSAGES
// =============================================================================

interface RiskMetricsUpdate {
  instrumentId: number;
  symbol: string;
  var1d: number;
  var5d: number;
  volatility: number;
  beta?: number;
  sharpeRatio?: number;
  maxDrawdown?: number;
  calculatedAt: string;
}

interface RiskMetricsMessage extends WebSocketMessage {
  messageType: 'risk_metrics';
  data: RiskMetricsUpdate;
}

// =============================================================================
// CONNECTION MANAGEMENT MESSAGES
// =============================================================================

interface ConnectionStatus {
  clientId: string;
  connectedAt: string;
  subscriptions: string[];
  lastHeartbeat: string;
  connectionQuality?: string;
  messageCount?: number;
}

interface ConnectionMessage extends WebSocketMessage {
  messageType: 'connection_status';
  data: ConnectionStatus;
}

interface ErrorDetails {
  errorCode: string;
  errorMessage: string;
  requestId?: string;
  timestamp: string;
  severity: 'warning' | 'error' | 'critical';
  retryAfter?: number;
}

interface ErrorMessage extends WebSocketMessage {
  messageType: 'error';
  data: ErrorDetails;
}

// =============================================================================
// SUBSCRIPTION MESSAGES
// =============================================================================

interface SubscriptionRequest {
  subscriptionType: string;
  instrumentId?: number;
  parameters?: Record<string, any>;
  requestId?: string;
}

interface SubscriptionMessage extends WebSocketMessage {
  messageType: 'subscribe';
  data: SubscriptionRequest;
}

interface UnsubscriptionRequest {
  subscriptionType: string;
  instrumentId?: number;
  requestId?: string;
}

interface UnsubscriptionMessage extends WebSocketMessage {
  messageType: 'unsubscribe';
  data: UnsubscriptionRequest;
}

interface SubscriptionAcknowledgment {
  subscriptionType: string;
  instrumentId?: number;
  status: 'subscribed' | 'unsubscribed' | 'failed';
  message?: string;
  requestId?: string;
}

interface SubscriptionAckMessage extends WebSocketMessage {
  messageType: 'subscription_ack';
  data: SubscriptionAcknowledgment;
}

// =============================================================================
// HEARTBEAT MESSAGES
// =============================================================================

interface PingData {
  clientTime: string;
  sequence?: number;
}

interface PingMessage extends WebSocketMessage {
  messageType: 'ping';
  data: PingData;
}

interface PongData {
  clientTime: string;
  serverTime: string;
  sequence?: number;
  latencyMs?: number;
}

interface PongMessage extends WebSocketMessage {
  messageType: 'pong';
  data: PongData;
}

// =============================================================================
// MESSAGE UNIONS
// =============================================================================

// Incoming messages (from server to client)
export type IncomingMessage = 
  | MarketDataMessage
  | AlertMessage
  | AnalyticsMessage
  | TechnicalIndicatorMessage
  | PricePredictionMessage
  | RiskMetricsMessage
  | ConnectionMessage
  | ErrorMessage
  | SubscriptionAckMessage
  | PongMessage;

// Outgoing messages (from client to server)
export type OutgoingMessage = 
  | PingMessage
  | SubscriptionMessage
  | UnsubscriptionMessage;

// All message types
export type AllMessages = IncomingMessage | OutgoingMessage;

// =============================================================================
// MESSAGE VALIDATION UTILITIES
// =============================================================================

/**
 * Type guard to check if a message is a valid incoming message.
 */
export function isValidIncomingMessage(message: any): message is IncomingMessage {
  return (
    typeof message === 'object' &&
    message !== null &&
    typeof message.messageType === 'string' &&
    typeof message.version === 'string' &&
    typeof message.timestamp === 'string' &&
    message.data !== undefined
  );
}

/**
 * Type guard for specific message types.
 */
export function isMarketDataMessage(message: IncomingMessage): message is MarketDataMessage {
  return message.messageType === 'market_data';
}

export function isAnalyticsMessage(message: IncomingMessage): message is AnalyticsMessage {
  return message.messageType === 'analytics_update';
}

export function isTechnicalIndicatorMessage(message: IncomingMessage): message is TechnicalIndicatorMessage {
  return message.messageType === 'technical_indicators';
}

export function isAlertMessage(message: IncomingMessage): message is AlertMessage {
  return message.messageType === 'alert';
}

export function isPricePredictionMessage(message: IncomingMessage): message is PricePredictionMessage {
  return message.messageType === 'price_prediction';
}

export function isRiskMetricsMessage(message: IncomingMessage): message is RiskMetricsMessage {
  return message.messageType === 'risk_metrics';
}

export function isConnectionMessage(message: IncomingMessage): message is ConnectionMessage {
  return message.messageType === 'connection_status';
}

export function isErrorMessage(message: IncomingMessage): message is ErrorMessage {
  return message.messageType === 'error';
}

export function isPongMessage(message: IncomingMessage): message is PongMessage {
  return message.messageType === 'pong';
}

// =============================================================================
// MESSAGE CREATION UTILITIES
// =============================================================================

/**
 * Create a ping message with current timestamp.
 */
export function createPingMessage(sequence?: number): PingMessage {
  return {
    messageType: 'ping',
    version: '1.0',
    timestamp: new Date().toISOString(),
    data: {
      clientTime: new Date().toISOString(),
      sequence
    }
  };
}

/**
 * Create a subscription message.
 */
export function createSubscriptionMessage(
  subscriptionType: string,
  instrumentId?: number,
  parameters?: Record<string, any>,
  requestId?: string
): SubscriptionMessage {
  return {
    messageType: 'subscribe',
    version: '1.0',
    timestamp: new Date().toISOString(),
    data: {
      subscriptionType,
      instrumentId,
      parameters,
      requestId: requestId || `sub_${Date.now()}_${Math.random()}`
    }
  };
}

/**
 * Create an unsubscription message.
 */
export function createUnsubscriptionMessage(
  subscriptionType: string,
  instrumentId?: number,
  requestId?: string
): UnsubscriptionMessage {
  return {
    messageType: 'unsubscribe',
    version: '1.0',
    timestamp: new Date().toISOString(),
    data: {
      subscriptionType,
      instrumentId,
      requestId: requestId || `unsub_${Date.now()}_${Math.random()}`
    }
  };
}

// =============================================================================
// PERFORMANCE TRACKING TYPES
// =============================================================================

export interface WebSocketPerformanceMetrics {
  messagesReceived: number;
  averageProcessingTime: number;
  errorRate: number;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
  lastMessageTimestamp?: string;
}

export interface MessageProcessingStats {
  messageType: string;
  count: number;
  averageProcessingTime: number;
  errorCount: number;
}

// =============================================================================
// SUBSCRIPTION MANAGEMENT TYPES
// =============================================================================

export interface SubscriptionState {
  subscriptionType: string;
  instrumentId?: number;
  status: 'subscribing' | 'subscribed' | 'unsubscribing' | 'unsubscribed' | 'error';
  lastUpdate?: string;
  errorMessage?: string;
}

export interface WebSocketSubscriptions {
  [key: string]: SubscriptionState;
}

// Export commonly used interfaces
export type {
  WebSocketMessage,
  MarketDataUpdate,
  AnalyticsUpdate,
  TechnicalIndicatorUpdate,
  PricePredictionUpdate,
  RiskMetricsUpdate,
  AlertNotification,
  ConnectionStatus,
  ErrorDetails,
  SubscriptionRequest,
  PingData,
  PongData
};