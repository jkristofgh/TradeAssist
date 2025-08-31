/**
 * TypeScript type definitions for TradeAssist Frontend
 * 
 * These types correspond to the backend SQLAlchemy models and API responses
 * to ensure type safety across the full stack.
 */

// Export historical data types
export * from './historicalData';

// =============================================================================
// ENUMS
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
// BASE MODELS
// =============================================================================

export interface Instrument {
  id: number;
  symbol: string;
  name: string;
  type: InstrumentType;
  status: InstrumentStatus;
  last_tick?: string | null; // ISO datetime string
  last_price?: number | null;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface MarketData {
  id: number;
  timestamp: string; // ISO datetime string
  instrument_id: number;
  price?: number | null;
  volume?: number | null;
  bid?: number | null;
  ask?: number | null;
  bid_size?: number | null;
  ask_size?: number | null;
  open_price?: number | null;
  high_price?: number | null;
  low_price?: number | null;
}

export interface AlertRule {
  id: number;
  instrument_id: number;
  rule_type: RuleType;
  condition: RuleCondition;
  threshold: number;
  active: boolean;
  name?: string | null;
  description?: string | null;
  time_window_seconds?: number | null;
  moving_average_period?: number | null;
  cooldown_seconds: number;
  last_triggered?: string | null; // ISO datetime string
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface AlertLog {
  id: number;
  timestamp: string; // ISO datetime string
  rule_id: number;
  instrument_id: number;
  trigger_value: number;
  threshold_value: number;
  fired_status: AlertStatus;
  delivery_status: DeliveryStatus;
  evaluation_time_ms?: number | null;
  rule_condition: RuleCondition;
  alert_message?: string | null;
  error_message?: string | null;
  delivery_attempted_at?: string | null; // ISO datetime string
  delivery_completed_at?: string | null; // ISO datetime string
}

// =============================================================================
// EXTENDED MODELS WITH RELATIONSHIPS
// =============================================================================

export interface InstrumentWithDetails extends Instrument {
  market_data?: MarketData[];
  alert_rules?: AlertRule[];
  alert_logs?: AlertLog[];
}

export interface AlertRuleWithDetails extends AlertRule {
  instrument?: Instrument;
  alert_logs?: AlertLog[];
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
  per_page: number;
  pages: number;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  ingestion_active: boolean;
  last_tick: string | null;
  api_connected: boolean;
  active_instruments: number;
  total_rules: number;
  last_alert: string | null;
  historical_data_service?: {
    status: 'healthy' | 'degraded' | 'unhealthy';
    service_running: boolean;
    schwab_client_connected?: boolean;
    cache_size?: number;
    total_requests?: number;
    database_healthy?: boolean;
    data_freshness_minutes?: number;
    error?: string;
  } | null;
}

export interface AlertStats {
  total_alerts: number;
  alerts_today: number;
  alerts_last_hour: number;
  avg_evaluation_time_ms?: number;
  success_rate_24h: number;
  alerts_by_status: Record<AlertStatus, number>;
  alerts_by_delivery_status: Record<DeliveryStatus, number>;
  top_triggered_rules: Array<{
    rule_id: number;
    rule_name: string;
    count: number;
  }>;
  // Additional fields that might be used in SystemHealth
  total_alerts_this_week?: number;
  total_alerts_today?: number;
  fastest_evaluation_ms?: number;
  slowest_evaluation_ms?: number;
}

// =============================================================================
// WEBSOCKET MESSAGE TYPES
// =============================================================================

export interface WebSocketMessage {
  type: 'tick_update' | 'alert_fired' | 'health_status' | 'ping' | 'pong';
  timestamp: string;
}

export interface TickUpdateMessage extends WebSocketMessage {
  type: 'tick_update';
  data: {
    instrument_id: number;
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
    alert_id: number;
    rule_id: number;
    instrument_id: number;
    symbol: string;
    trigger_value: number;
    threshold_value: number;
    rule_condition: RuleCondition;
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
// FORM TYPES
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
  instrument_id: number;
  rule_type: RuleType;
  condition: RuleCondition;
  threshold: number;
  active?: boolean;
  name?: string;
  description?: string;
  time_window_seconds?: number;
  moving_average_period?: number;
  cooldown_seconds?: number;
}

export interface UpdateAlertRuleRequest {
  rule_type?: RuleType;
  condition?: RuleCondition;
  threshold?: number;
  active?: boolean;
  name?: string;
  description?: string;
  time_window_seconds?: number;
  moving_average_period?: number;
  cooldown_seconds?: number;
}

// =============================================================================
// FILTER/QUERY TYPES
// =============================================================================

export interface InstrumentFilters {
  type?: InstrumentType;
  status?: InstrumentStatus;
  symbol_contains?: string;
}

export interface AlertRuleFilters {
  instrument_id?: number;
  rule_type?: RuleType;
  active?: boolean;
  condition?: RuleCondition;
}

export interface AlertLogFilters {
  instrument_id?: number;
  rule_id?: number;
  fired_status?: AlertStatus;
  delivery_status?: DeliveryStatus;
  start_date?: string;
  end_date?: string;
}

export interface PaginationParams {
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// =============================================================================
// UI STATE TYPES
// =============================================================================

export interface LoadingState {
  isLoading: boolean;
  error?: string | null;
}

export interface WebSocketState {
  isConnected: boolean;
  connectionId?: string;
  lastPing?: number;
  reconnectAttempts: number;
  error?: string | null;
}

export interface DashboardState {
  instruments: Instrument[];
  realtimeData: Record<number, MarketData>;
  activeAlerts: AlertLogWithDetails[];
  systemHealth: HealthStatus | null;
}

export interface FormValidationError {
  field: string;
  message: string;
}

export interface FormState<T> {
  data: T;
  errors: FormValidationError[];
  isSubmitting: boolean;
  isDirty: boolean;
}

// =============================================================================
// UTILITY TYPES
// =============================================================================

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};