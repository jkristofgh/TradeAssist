/**
 * Historical Data Service
 * 
 * Service for interacting with the historical data API endpoints.
 * Provides methods for fetching historical market data, managing saved queries,
 * and retrieving data frequencies and sources.
 */

import { apiClient, ApiError } from './apiClient';

// =============================================================================
// TYPE DEFINITIONS
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

export interface HistoricalDataRequest {
  symbols: string[];
  start_date?: string;
  end_date?: string;
  frequency?: DataFrequency;
  include_extended_hours?: boolean;
  max_records?: number;
  asset_class?: 'stock' | 'index' | 'future';
  continuous_series?: boolean;
  roll_policy?: 'calendar' | 'volume' | 'open_interest';
}

export interface MarketDataBar {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  vwap?: number;
  trades?: number;
  open_interest?: number;
  contract_month?: string;
  quality_score?: number;
}

export interface HistoricalDataResponse {
  data: MarketDataBar[];
  symbols: string[];
  frequency: string;
  start_date: string;
  end_date: string;
  total_records: number;
  cached: boolean;
  query_time_ms: number;
  source?: string;
}

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

export interface DataSource {
  id: number;
  name: string;
  provider_type: string;
  base_url: string;
  api_key_required: boolean;
  rate_limit_per_minute: number;
  capabilities: string[];
  configuration?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ServiceStats {
  total_queries: number;
  cache_hits: number;
  cache_misses: number;
  average_response_time_ms: number;
  active_connections: number;
  error_rate: number;
  last_reset: string;
}

export interface ServiceHealth {
  status: string;
  service_name: string;
  version: string;
  uptime_seconds: number;
  dependencies: {
    database: boolean;
    schwab_api: boolean;
    cache: boolean;
  };
  stats: ServiceStats;
}

// =============================================================================
// HISTORICAL DATA SERVICE CLASS
// =============================================================================

class HistoricalDataService {
  private baseEndpoint = '/api/v1/historical-data';

  // =============================================================================
  // DATA FETCHING
  // =============================================================================

  /**
   * Fetch historical market data
   */
  async fetchData(request: HistoricalDataRequest): Promise<HistoricalDataResponse> {
    try {
      const response = await (apiClient as any).post<HistoricalDataResponse>(
        `${this.baseEndpoint}/fetch`,
        request
      );
      return response;
    } catch (error) {
      if (error instanceof ApiError) {
        throw this.handleApiError(error);
      }
      throw error;
    }
  }

  /**
   * Get available data frequencies
   */
  async getFrequencies(): Promise<string[]> {
    try {
      const response = await (apiClient as any).get<string[]>(`${this.baseEndpoint}/frequencies`);
      return response;
    } catch (error) {
      if (error instanceof ApiError) {
        throw this.handleApiError(error);
      }
      throw error;
    }
  }

  /**
   * Get available data sources
   */
  async getSources(): Promise<DataSource[]> {
    try {
      const response = await (apiClient as any).get<DataSource[]>(`${this.baseEndpoint}/sources`);
      return response;
    } catch (error) {
      if (error instanceof ApiError) {
        throw this.handleApiError(error);
      }
      throw error;
    }
  }

  // =============================================================================
  // QUERY MANAGEMENT
  // =============================================================================

  /**
   * Save a query configuration
   */
  async saveQuery(request: SaveQueryRequest): Promise<SavedQuery> {
    try {
      const response = await (apiClient as any).post<SavedQuery>(
        `${this.baseEndpoint}/queries/save`,
        request
      );
      return response;
    } catch (error) {
      if (error instanceof ApiError) {
        throw this.handleApiError(error);
      }
      throw error;
    }
  }

  /**
   * Load a saved query
   */
  async loadQuery(queryId: number): Promise<SavedQuery> {
    try {
      const response = await (apiClient as any).get<SavedQuery>(
        `${this.baseEndpoint}/queries/${queryId}`
      );
      return response;
    } catch (error) {
      if (error instanceof ApiError) {
        throw this.handleApiError(error);
      }
      throw error;
    }
  }

  /**
   * Get all saved queries
   */
  async getSavedQueries(): Promise<SavedQuery[]> {
    try {
      const response = await (apiClient as any).get<SavedQuery[]>(`${this.baseEndpoint}/queries`);
      return response;
    } catch (error) {
      if (error instanceof ApiError) {
        throw this.handleApiError(error);
      }
      throw error;
    }
  }

  /**
   * Update a saved query
   */
  async updateQuery(queryId: number, request: Partial<SaveQueryRequest>): Promise<SavedQuery> {
    try {
      const response = await (apiClient as any).put<SavedQuery>(
        `${this.baseEndpoint}/queries/${queryId}`,
        request
      );
      return response;
    } catch (error) {
      if (error instanceof ApiError) {
        throw this.handleApiError(error);
      }
      throw error;
    }
  }

  /**
   * Delete a saved query
   */
  async deleteQuery(queryId: number): Promise<void> {
    try {
      await (apiClient as any).delete<void>(`${this.baseEndpoint}/queries/${queryId}`);
    } catch (error) {
      if (error instanceof ApiError) {
        throw this.handleApiError(error);
      }
      throw error;
    }
  }

  // =============================================================================
  // SERVICE MONITORING
  // =============================================================================

  /**
   * Get service statistics
   */
  async getStats(): Promise<ServiceStats> {
    try {
      const response = await (apiClient as any).get<ServiceStats>(`${this.baseEndpoint}/stats`);
      return response;
    } catch (error) {
      if (error instanceof ApiError) {
        throw this.handleApiError(error);
      }
      throw error;
    }
  }

  /**
   * Get service health status
   */
  async getHealth(): Promise<ServiceHealth> {
    try {
      const response = await (apiClient as any).get<ServiceHealth>(`${this.baseEndpoint}/health`);
      return response;
    } catch (error) {
      if (error instanceof ApiError) {
        throw this.handleApiError(error);
      }
      throw error;
    }
  }

  // =============================================================================
  // DATA EXPORT
  // =============================================================================

  /**
   * Export data to CSV format
   */
  async exportToCSV(data: MarketDataBar[]): Promise<Blob> {
    const headers = ['Symbol', 'Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'VWAP'];
    const csvContent = [
      headers.join(','),
      ...data.map(bar => [
        bar.symbol,
        bar.timestamp,
        bar.open,
        bar.high,
        bar.low,
        bar.close,
        bar.volume,
        bar.vwap || ''
      ].join(','))
    ].join('\n');

    return new Blob([csvContent], { type: 'text/csv' });
  }

  /**
   * Export data to JSON format
   */
  async exportToJSON(data: MarketDataBar[]): Promise<Blob> {
    const jsonContent = JSON.stringify(data, null, 2);
    return new Blob([jsonContent], { type: 'application/json' });
  }

  // =============================================================================
  // ERROR HANDLING
  // =============================================================================

  private handleApiError(error: ApiError): Error {
    if (error.isValidationError) {
      const details = error.data?.detail || [];
      const messages = Array.isArray(details)
        ? details.map((d: any) => `${d.loc?.join('.')}: ${d.msg}`).join(', ')
        : error.message;
      return new Error(`Validation error: ${messages}`);
    }

    if (error.status === 429) {
      return new Error('Rate limit exceeded. Please try again later.');
    }

    if (error.status === 503) {
      return new Error('Historical data service is temporarily unavailable.');
    }

    return error;
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

export const historicalDataService = new HistoricalDataService();

// =============================================================================
// REACT QUERY HELPERS
// =============================================================================

export const queryKeys = {
  historicalData: (request: HistoricalDataRequest) => ['historicalData', request] as const,
  frequencies: () => ['historicalData', 'frequencies'] as const,
  sources: () => ['historicalData', 'sources'] as const,
  savedQueries: () => ['historicalData', 'savedQueries'] as const,
  savedQuery: (id: number) => ['historicalData', 'savedQuery', id] as const,
  stats: () => ['historicalData', 'stats'] as const,
  health: () => ['historicalData', 'health'] as const,
};