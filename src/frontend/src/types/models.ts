/**
 * Comprehensive TypeScript interfaces for TradeAssist Frontend
 * 
 * These interfaces match the backend Pydantic models with camelCase field names
 * and include analytics API request/response models for complete type safety.
 */

// =============================================================================
// ENUMS (matching backend exactly)
// =============================================================================

export enum InstrumentType {
  FUTURE = 'future',
  INDEX = 'index',
  INTERNAL = 'internal'
}

export enum InstrumentStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  ERROR = 'error'
}

export enum RuleType {
  THRESHOLD = 'threshold',
  CROSSOVER = 'crossover',
  RATE_OF_CHANGE = 'rate_of_change',
  VOLUME_SPIKE = 'volume_spike',
  MULTI_CONDITION = 'multi_condition'
}

export enum RuleCondition {
  ABOVE = 'above',
  BELOW = 'below',
  EQUALS = 'equals',
  CROSSES_ABOVE = 'crosses_above',
  CROSSES_BELOW = 'crosses_below',
  PERCENT_CHANGE_UP = 'percent_change_up',
  PERCENT_CHANGE_DOWN = 'percent_change_down',
  VOLUME_ABOVE = 'volume_above'
}

export enum AlertStatus {
  FIRED = 'fired',
  SUPPRESSED = 'suppressed',
  ERROR = 'error'
}

export enum DeliveryStatus {
  PENDING = 'pending',
  IN_APP_SENT = 'in_app_sent',
  SOUND_PLAYED = 'sound_played',
  SLACK_SENT = 'slack_sent',
  ALL_DELIVERED = 'all_delivered',
  FAILED = 'failed'
}

// =============================================================================
// CORE MODEL INTERFACES (camelCase)
// =============================================================================

export interface Instrument {
  id: number;
  symbol: string;
  name: string;
  type: InstrumentType;
  status: InstrumentStatus;
  lastTick?: string | null; // ISO datetime string
  lastPrice?: number | null;
  createdAt: string; // ISO datetime string
  updatedAt: string; // ISO datetime string
}

export interface MarketData {
  id: number;
  timestamp: string; // ISO datetime string
  instrumentId: number;
  price?: number | null;
  volume?: number | null;
  bid?: number | null;
  ask?: number | null;
  bidSize?: number | null;
  askSize?: number | null;
  openPrice?: number | null;
  highPrice?: number | null;
  lowPrice?: number | null;
}

export interface AlertRule {
  id: number;
  instrumentId: number;
  instrumentSymbol: string; // ADDED: Missing field from requirements
  ruleType: RuleType;
  condition: RuleCondition;
  threshold: number;
  active: boolean;
  name?: string | null;
  description?: string | null;
  timeWindowSeconds?: number | null;
  movingAveragePeriod?: number | null;
  cooldownSeconds: number;
  lastTriggered?: string | null; // ISO datetime string
  createdAt: string; // ISO datetime string
  updatedAt: string; // ISO datetime string
}

export interface AlertLog {
  id: number;
  timestamp: string; // ISO datetime string
  ruleId: number;
  instrumentId: number;
  triggerValue: number;
  thresholdValue: number;
  firedStatus: AlertStatus;
  deliveryStatus: DeliveryStatus;
  evaluationTimeMs?: number | null;
  ruleCondition: RuleCondition;
  alertMessage?: string | null;
  errorMessage?: string | null;
  deliveryAttemptedAt?: string | null; // ISO datetime string
  deliveryCompletedAt?: string | null; // ISO datetime string
}

// =============================================================================
// ANALYTICS API REQUEST/RESPONSE MODELS
// =============================================================================

export interface AnalyticsRequest {
  instrumentId: number;
  lookbackHours?: number; // Default 24, range 1-8760
  indicators?: string[] | null;
}

export interface PredictionRequest {
  instrumentId: number;
  predictionHorizon: number; // hours
  modelType?: string;
}

export interface RiskRequest {
  instrumentId: number;
  timeframe?: string;
  confidenceLevel?: number;
}

export interface StressTestRequest {
  instrumentId: number;
  scenarios: string[];
  timeframe?: string;
}

export interface VolumeProfileRequest {
  instrumentId: number;
  timeframe?: string;
  binSize?: number;
}

// Technical Indicator Responses
export interface TechnicalIndicator {
  name: string;
  value: number;
  timestamp: string;
  parameters?: Record<string, any>;
}

export interface TechnicalIndicatorResponse {
  indicators: {
    rsi?: number;
    macd?: {
      macd: number;
      signal: number;
      histogram: number;
    };
    bollingerBands?: {
      upper: number;
      middle: number;
      lower: number;
    };
    movingAverages?: {
      sma20?: number;
      sma50?: number;
      ema12?: number;
      ema26?: number;
    };
    stochastic?: {
      k: number;
      d: number;
    };
    atr?: number;
  };
  timestamp: string;
}

export interface MarketAnalysisResponse {
  trend: string;
  confidence: number;
  indicators: TechnicalIndicator[];
  timestamp: string;
  summary?: string;
  signals?: Array<{
    type: string;
    strength: number;
    description: string;
  }>;
}

export interface PredictionResponse {
  predictedPrice: number;
  confidence: number;
  modelUsed: string;
  predictionHorizon: number;
  timestamp: string;
  priceRange?: {
    low: number;
    high: number;
  };
  factors?: Array<{
    name: string;
    impact: number;
    description: string;
  }>;
}

export interface AnomalyDetectionResponse {
  anomalies: Array<{
    timestamp: string;
    value: number;
    anomalyScore: number;
    type: string;
    description: string;
  }>;
  overallRisk: number;
  timeframe: string;
}

export interface TrendClassificationResponse {
  trend: 'bullish' | 'bearish' | 'sideways';
  strength: number;
  duration: string;
  confidence: number;
  trendLines?: Array<{
    type: 'support' | 'resistance';
    slope: number;
    intercept: number;
    confidence: number;
  }>;
  timestamp: string;
}

export interface VarCalculationResponse {
  var95: number;
  var99: number;
  expectedShortfall: number;
  timeframe: string;
  methodology: string;
  historicalPeriod: string;
  timestamp: string;
}

export interface RiskMetricsResponse {
  volatility: number;
  sharpeRatio?: number;
  maxDrawdown: number;
  beta?: number;
  var95: number;
  var99: number;
  timeframe: string;
  timestamp: string;
}

export interface StressTestResponse {
  scenarios: Array<{
    name: string;
    description: string;
    pnl: number;
    percentageChange: number;
    probability: number;
  }>;
  worstCase: {
    scenario: string;
    pnl: number;
    percentageChange: number;
  };
  timestamp: string;
}

export interface VolumeProfileResponse {
  profile: Array<{
    priceLevel: number;
    volume: number;
    percentage: number;
  }>;
  poc: number; // Point of Control
  valueAreaHigh: number;
  valueAreaLow: number;
  valueAreaVolume: number;
  timeframe: string;
  timestamp: string;
}

export interface CorrelationMatrixResponse {
  correlations: Record<string, Record<string, number>>;
  instruments: string[];
  timeframe: string;
  timestamp: string;
}

export interface MarketMicrostructureResponse {
  bidAskSpread: {
    current: number;
    average: number;
    volatility: number;
  };
  orderBookImbalance: number;
  priceImpact: number;
  marketDepth: {
    bidDepth: number;
    askDepth: number;
    totalDepth: number;
  };
  timestamp: string;
}

// =============================================================================
// EXTENDED MODELS WITH RELATIONSHIPS
// =============================================================================

export interface InstrumentWithDetails extends Instrument {
  marketData?: MarketData[];
  alertRules?: AlertRule[];
  alertLogs?: AlertLog[];
}

export interface AlertRuleWithDetails extends AlertRule {
  instrument?: Instrument;
  alertLogs?: AlertLog[];
}

export interface AlertLogWithDetails extends AlertLog {
  rule?: AlertRule;
  instrument?: Instrument;
}

// =============================================================================
// API RESPONSE TYPES
// =============================================================================

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  perPage: number;
  pages: number;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  ingestionActive: boolean;
  lastTick: string | null;
  apiConnected: boolean;
  activeInstruments: number;
  totalRules: number;
  lastAlert: string | null;
  historicalDataService?: {
    status: 'healthy' | 'degraded' | 'unhealthy';
    serviceRunning: boolean;
    schwabClientConnected?: boolean;
    cacheSize?: number;
    totalRequests?: number;
    databaseHealthy?: boolean;
    dataFreshnessMinutes?: number;
    error?: string;
  } | null;
}

export interface AlertStats {
  totalAlerts: number;
  alertsToday: number;
  alertsLastHour: number;
  avgEvaluationTimeMs?: number;
  successRate24h: number;
  alertsByStatus: Record<AlertStatus, number>;
  alertsByDeliveryStatus: Record<DeliveryStatus, number>;
  topTriggeredRules: Array<{
    ruleId: number;
    ruleName: string;
    count: number;
  }>;
  // Additional fields that might be used in SystemHealth
  totalAlertsThisWeek?: number;
  totalAlertsToday?: number;
  fastestEvaluationMs?: number;
  slowestEvaluationMs?: number;
}

// =============================================================================
// WEBSOCKET STATE AND MESSAGE TYPES (camelCase)
// =============================================================================

export interface WebSocketState {
  isConnected: boolean;
  reconnectAttempts: number;
  error: string | null;
}

export interface WebSocketMessage {
  type: 'tick_update' | 'alert_fired' | 'health_status' | 'ping' | 'pong';
  timestamp: string;
}

export interface TickUpdateMessage extends WebSocketMessage {
  type: 'tick_update';
  data: {
    instrumentId: number;
    symbol: string;
    price: number;
    volume?: number;
    bid?: number;
    ask?: number;
    timestamp: string;
  };
}

export interface AlertFiredMessage extends WebSocketMessage {
  type: 'alert_fired';
  data: {
    alertId: number;
    ruleId: number;
    instrumentId: number;
    symbol: string;
    triggerValue: number;
    thresholdValue: number;
    ruleCondition: RuleCondition;
    message: string;
  };
}

export interface HealthStatusMessage extends WebSocketMessage {
  type: 'health_status';
  data: HealthStatus;
}

export interface PingMessage extends WebSocketMessage {
  type: 'ping';
}

export interface PongMessage extends WebSocketMessage {
  type: 'pong';
}

export type WebSocketIncomingMessage = 
  | TickUpdateMessage 
  | AlertFiredMessage 
  | HealthStatusMessage 
  | PongMessage;

// =============================================================================
// FORM REQUEST TYPES (camelCase)
// =============================================================================

export interface CreateInstrumentRequest {
  symbol: string;
  name: string;
  type: InstrumentType;
  status?: InstrumentStatus;
}

export interface UpdateInstrumentRequest {
  name?: string;
  type?: InstrumentType;
  status?: InstrumentStatus;
}

export interface CreateAlertRuleRequest {
  instrumentId: number;
  instrumentSymbol: string; // ADDED: Required field
  ruleType: RuleType;
  condition: RuleCondition;
  threshold: number;
  active?: boolean;
  name?: string;
  description?: string;
  timeWindowSeconds?: number;
  movingAveragePeriod?: number;
  cooldownSeconds?: number;
}

export interface UpdateAlertRuleRequest {
  ruleType?: RuleType;
  condition?: RuleCondition;
  threshold?: number;
  active?: boolean;
  name?: string;
  description?: string;
  instrumentSymbol?: string; // ADDED: Optional field for updates
  timeWindowSeconds?: number;
  movingAveragePeriod?: number;
  cooldownSeconds?: number;
}

// =============================================================================
// FILTER/QUERY TYPES (camelCase)
// =============================================================================

export interface InstrumentFilters {
  type?: InstrumentType;
  status?: InstrumentStatus;
  symbolContains?: string;
}

export interface AlertRuleFilters {
  instrumentId?: number;
  ruleType?: RuleType;
  active?: boolean;
  condition?: RuleCondition;
}

export interface AlertLogFilters {
  instrumentId?: number;
  ruleId?: number;
  firedStatus?: AlertStatus;
  deliveryStatus?: DeliveryStatus;
  startDate?: string;
  endDate?: string;
}

export interface PaginationParams {
  page?: number;
  perPage?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// =============================================================================
// UTILITY TYPES FOR TYPE TRANSFORMATIONS
// =============================================================================

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// Type utility to convert snake_case to camelCase at type level
export type CamelCase<S extends string> = S extends `${infer P1}_${infer P2}${infer P3}`
  ? `${P1}${Capitalize<CamelCase<`${P2}${P3}`>>}`
  : S;

// Type utility to convert camelCase to snake_case at type level  
export type SnakeCase<S extends string> = S extends `${infer T}${infer U}`
  ? `${T extends Capitalize<T> ? "_" : ""}${Lowercase<T>}${SnakeCase<U>}`
  : S;

// Convert object keys from snake_case to camelCase
export type CamelCaseKeys<T> = {
  [K in keyof T as CamelCase<string & K>]: T[K] extends object ? CamelCaseKeys<T[K]> : T[K];
};

// Convert object keys from camelCase to snake_case  
export type SnakeCaseKeys<T> = {
  [K in keyof T as SnakeCase<string & K>]: T[K] extends object ? SnakeCaseKeys<T[K]> : T[K];
};