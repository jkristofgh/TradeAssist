/**
 * Historical Data Type Definitions
 * 
 * TypeScript interfaces and types for historical data components and services.
 */

import { MarketDataBar } from '../services/historicalDataService';

// =============================================================================
// ENUMS
// =============================================================================

export enum DataFrequency {
  ONE_MIN = '1min',
  FIVE_MIN = '5min',
  FIFTEEN_MIN = '15min',
  THIRTY_MIN = '30min',
  ONE_HOUR = '1h',
  FOUR_HOUR = '4h',
  ONE_DAY = '1d',
  ONE_WEEK = '1w',
  ONE_MONTH = '1M'
}

export enum AssetClass {
  STOCK = 'stock',
  INDEX = 'index',
  FUTURE = 'future'
}

export enum RollPolicy {
  CALENDAR = 'calendar',
  VOLUME = 'volume',
  OPEN_INTEREST = 'open_interest'
}

export enum TimeRangePreset {
  TODAY = 'today',
  YESTERDAY = 'yesterday',
  LAST_7_DAYS = 'last_7_days',
  LAST_30_DAYS = 'last_30_days',
  LAST_90_DAYS = 'last_90_days',
  LAST_YEAR = 'last_year',
  CUSTOM = 'custom'
}

// =============================================================================
// QUERY INTERFACES
// =============================================================================

export interface HistoricalDataQuery {
  symbols: string[];
  startDate?: Date;
  endDate?: Date;
  frequency: DataFrequency;
  assetClass?: AssetClass;
  includeExtendedHours?: boolean;
  maxRecords?: number;
  continuousSeries?: boolean;
  rollPolicy?: RollPolicy;
}

export interface QueryFormData {
  symbols: string;
  timeRange: TimeRangePreset;
  customStartDate?: string;
  customEndDate?: string;
  frequency: DataFrequency;
  assetClass: AssetClass;
  includeExtendedHours: boolean;
  maxRecords: number;
  continuousSeries: boolean;
  rollPolicy: RollPolicy;
}

// =============================================================================
// DATA INTERFACES
// =============================================================================

// MarketDataBar, SymbolDataResponse, and HistoricalDataResponse 
// are now defined in historicalDataService.ts to avoid duplication

// =============================================================================
// SAVED QUERY INTERFACES
// =============================================================================

export interface SavedQuery {
  id: number;
  name: string;
  description?: string;
  symbols: string[];
  frequency: string;
  filters?: Record<string, any>;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
  last_executed?: string;
  execution_count: number;
}

export interface SaveQueryRequest {
  name: string;
  description?: string;
  symbols: string[];
  frequency: string;
  filters?: Record<string, any>;
  is_favorite?: boolean;
}

export interface QueryFilters {
  assetClass?: AssetClass;
  includeExtendedHours?: boolean;
  continuousSeries?: boolean;
  rollPolicy?: RollPolicy;
  [key: string]: any;
}

// =============================================================================
// COMPONENT PROPS
// =============================================================================

export interface QueryFormProps {
  onSubmit: (query: HistoricalDataQuery) => void;
  initialValues?: Partial<QueryFormData>;
  isLoading?: boolean;
  frequencies?: DataFrequency[];
}

export interface DataPreviewProps {
  data: MarketDataBar[];
  query: HistoricalDataQuery;
  isLoading?: boolean;
  onSaveQuery?: (name: string, description?: string) => void;
  onExport?: (format: 'csv' | 'json') => void;
  onRerun?: () => void;
}

export interface SavedQueriesProps {
  queries: SavedQuery[];
  onLoad: (query: SavedQuery) => void;
  onEdit: (query: SavedQuery) => void;
  onDelete: (queryId: number) => void;
  onToggleFavorite: (queryId: number, isFavorite: boolean) => void;
  isLoading?: boolean;
}

export interface HistoricalDataPageProps {
  defaultTab?: 'new' | 'saved';
}

// =============================================================================
// CHART INTERFACES
// =============================================================================

export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  borderColor?: string;
  backgroundColor?: string;
  fill?: boolean;
  type?: 'line' | 'bar' | 'candlestick';
}

export interface CandlestickData {
  x: string | Date;
  o: number;
  h: number;
  l: number;
  c: number;
}

// =============================================================================
// TABLE INTERFACES
// =============================================================================

export interface TableColumn {
  key: keyof MarketDataBar;
  label: string;
  sortable?: boolean;
  format?: (value: any) => string;
  align?: 'left' | 'center' | 'right';
}

export interface TableSortConfig {
  key: keyof MarketDataBar;
  direction: 'asc' | 'desc';
}

export interface TablePaginationConfig {
  page: number;
  pageSize: number;
  totalPages: number;
  totalRecords: number;
}

// =============================================================================
// VALIDATION INTERFACES
// =============================================================================

export interface ValidationError {
  field: string;
  message: string;
}

export interface FormValidation {
  isValid: boolean;
  errors: ValidationError[];
}

// =============================================================================
// SERVICE INTERFACES
// =============================================================================

export interface DataSource {
  id: number;
  name: string;
  providerType: string;
  baseUrl: string;
  apiKeyRequired: boolean;
  rateLimitPerMinute: number;
  capabilities: string[];
  configuration?: Record<string, any>;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ServiceStats {
  totalQueries: number;
  cacheHits: number;
  cacheMisses: number;
  averageResponseTimeMs: number;
  activeConnections: number;
  errorRate: number;
  lastReset: string;
}

export interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  serviceName: string;
  version: string;
  uptimeSeconds: number;
  dependencies: {
    database: boolean;
    schwabApi: boolean;
    cache: boolean;
  };
  stats: ServiceStats;
}

// =============================================================================
// UTILITY TYPES
// =============================================================================

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

export interface PaginatedData<T> {
  items: T[];
  pagination: TablePaginationConfig;
}

// =============================================================================
// EXPORT FORMATS
// =============================================================================

export type ExportFormat = 'csv' | 'json' | 'xlsx';

export interface ExportOptions {
  format: ExportFormat;
  fileName?: string;
  includeHeaders?: boolean;
  dateFormat?: string;
}