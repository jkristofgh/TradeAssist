/**
 * API Client Service
 * 
 * Centralized HTTP client for communicating with the TradeAssist FastAPI backend.
 * Provides type-safe methods for all backend endpoints with proper error handling,
 * request/response transformation, and optimistic updates.
 */

import {
  Instrument,
  InstrumentWithDetails,
  AlertRule,
  AlertRuleWithDetails,
  AlertLog,
  AlertLogWithDetails,
  HealthStatus,
  AlertStats,
  CreateInstrumentRequest,
  UpdateInstrumentRequest,
  CreateAlertRuleRequest,
  UpdateAlertRuleRequest,
  InstrumentFilters,
  AlertRuleFilters,
  AlertLogFilters,
  PaginationParams,
  PaginatedResponse,
  ApiResponse,
  // Analytics types
  AnalyticsRequest,
  PredictionRequest,
  RiskRequest,
  StressTestRequest,
  VolumeProfileRequest,
  MarketAnalysisResponse,
  TechnicalIndicatorResponse,
  PredictionResponse,
  AnomalyDetectionResponse,
  TrendClassificationResponse,
  VarCalculationResponse,
  RiskMetricsResponse,
  StressTestResponse,
  VolumeProfileResponse,
  CorrelationMatrixResponse,
  MarketMicrostructureResponse
} from '../types/models';
import {
  transformApiResponse,
  transformApiRequest,
  TypedTransformer,
  extractErrorMessage
} from '../utils/typeTransforms';

// =============================================================================
// API CLIENT CLASS
// =============================================================================

export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  // =============================================================================
  // CORE HTTP METHODS
  // =============================================================================

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      // Handle non-JSON responses (like 204 No Content)
      if (response.status === 204) {
        return {} as T;
      }

      const data = await response.json();

      if (!response.ok) {
        // Transform error data for consistency
        const errorData = transformApiResponse(data);
        throw new ApiError(
          response.status,
          extractErrorMessage(errorData),
          errorData
        );
      }

      // Transform response data from snake_case to camelCase
      return transformApiResponse<T>(data);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }

      // Network or parsing errors
      throw new ApiError(
        0,
        error instanceof Error ? error.message : 'Unknown error occurred',
        null
      );
    }
  }

  private async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = params ? `${endpoint}?${new URLSearchParams(this.serializeParams(params))}` : endpoint;
    return this.request<T>(url, { method: 'GET' });
  }

  private async post<T>(endpoint: string, data?: any): Promise<T> {
    const transformedData = data ? transformApiRequest(data) : undefined;
    return this.request<T>(endpoint, {
      method: 'POST',
      body: transformedData ? JSON.stringify(transformedData) : undefined,
    });
  }

  private async put<T>(endpoint: string, data?: any): Promise<T> {
    const transformedData = data ? transformApiRequest(data) : undefined;
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: transformedData ? JSON.stringify(transformedData) : undefined,
    });
  }

  private async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // =============================================================================
  // HEALTH API
  // =============================================================================

  async getHealth(): Promise<HealthStatus> {
    return this.get<HealthStatus>('/api/health');
  }

  async getDetailedHealth(): Promise<HealthStatus> {
    return this.get<HealthStatus>('/api/health/detailed');
  }

  // =============================================================================
  // INSTRUMENTS API
  // =============================================================================

  async getInstruments(filters?: InstrumentFilters): Promise<Instrument[]> {
    return this.get<Instrument[]>('/api/instruments', filters);
  }

  async getInstrument(id: number): Promise<InstrumentWithDetails> {
    return this.get<InstrumentWithDetails>(`/api/instruments/${id}`);
  }

  async createInstrument(data: CreateInstrumentRequest): Promise<Instrument> {
    return this.post<Instrument>('/api/instruments', data);
  }

  async updateInstrument(id: number, data: UpdateInstrumentRequest): Promise<Instrument> {
    return this.put<Instrument>(`/api/instruments/${id}`, data);
  }

  async deleteInstrument(id: number): Promise<void> {
    return this.delete<void>(`/api/instruments/${id}`);
  }

  // =============================================================================
  // ALERT RULES API
  // =============================================================================

  async getAlertRules(filters?: AlertRuleFilters): Promise<AlertRule[]> {
    return this.get<AlertRule[]>('/api/rules', filters);
  }

  async getAlertRule(id: number): Promise<AlertRuleWithDetails> {
    return this.get<AlertRuleWithDetails>(`/api/rules/${id}`);
  }

  async createAlertRule(data: CreateAlertRuleRequest): Promise<AlertRule> {
    return this.post<AlertRule>('/api/rules', data);
  }

  async updateAlertRule(id: number, data: UpdateAlertRuleRequest): Promise<AlertRule> {
    return this.put<AlertRule>(`/api/rules/${id}`, data);
  }

  async deleteAlertRule(id: number): Promise<void> {
    return this.delete<void>(`/api/rules/${id}`);
  }

  // Bulk operations
  async bulkUpdateAlertRules(updates: Array<{ id: number; data: UpdateAlertRuleRequest }>): Promise<AlertRule[]> {
    const promises = updates.map(({ id, data }) => this.updateAlertRule(id, data));
    return Promise.all(promises);
  }

  async bulkDeleteAlertRules(ids: number[]): Promise<void> {
    const promises = ids.map(id => this.deleteAlertRule(id));
    await Promise.all(promises);
  }

  async toggleAlertRules(ids: number[], active: boolean): Promise<AlertRule[]> {
    return this.bulkUpdateAlertRules(
      ids.map(id => ({ id, data: { active } }))
    );
  }

  // =============================================================================
  // ALERTS API
  // =============================================================================

  async getAlerts(
    filters?: AlertLogFilters,
    pagination?: PaginationParams
  ): Promise<PaginatedResponse<AlertLogWithDetails>> {
    const params = { ...filters, ...pagination };
    return this.get<PaginatedResponse<AlertLogWithDetails>>('/api/alerts', params);
  }

  async getAlertStats(): Promise<AlertStats> {
    return this.get<AlertStats>('/api/alerts/stats');
  }

  async deleteAlert(id: number): Promise<void> {
    return this.delete<void>(`/api/alerts/${id}`);
  }

  // Export alerts to CSV
  async exportAlerts(filters?: AlertLogFilters): Promise<Blob> {
    const params = { ...filters, format: 'csv' };
    const url = `${this.baseUrl}/api/alerts/export?${new URLSearchParams(this.serializeParams(params))}`;
    
    const response = await fetch(url, {
      headers: this.defaultHeaders,
    });

    if (!response.ok) {
      throw new ApiError(response.status, 'Failed to export alerts', null);
    }

    return response.blob();
  }

  // =============================================================================
  // ANALYTICS API
  // =============================================================================

  async getMarketAnalysis(request: AnalyticsRequest): Promise<MarketAnalysisResponse> {
    return this.post<MarketAnalysisResponse>('/api/analytics/market-analysis', request);
  }

  async getRealTimeIndicators(request: AnalyticsRequest): Promise<TechnicalIndicatorResponse> {
    return this.post<TechnicalIndicatorResponse>('/api/analytics/real-time-indicators', request);
  }

  async predictPrice(request: PredictionRequest): Promise<PredictionResponse> {
    return this.post<PredictionResponse>('/api/analytics/price-prediction', request);
  }

  async detectAnomalies(request: AnalyticsRequest): Promise<AnomalyDetectionResponse> {
    return this.post<AnomalyDetectionResponse>('/api/analytics/anomaly-detection', request);
  }

  async classifyTrend(request: AnalyticsRequest): Promise<TrendClassificationResponse> {
    return this.post<TrendClassificationResponse>('/api/analytics/trend-classification', request);
  }

  async calculateVar(request: RiskRequest): Promise<VarCalculationResponse> {
    return this.post<VarCalculationResponse>('/api/analytics/var-calculation', request);
  }

  async getRiskMetrics(request: RiskRequest): Promise<RiskMetricsResponse> {
    return this.post<RiskMetricsResponse>('/api/analytics/risk-metrics', request);
  }

  async performStressTest(request: StressTestRequest): Promise<StressTestResponse> {
    return this.post<StressTestResponse>('/api/analytics/stress-test', request);
  }

  async getVolumeProfile(request: VolumeProfileRequest): Promise<VolumeProfileResponse> {
    return this.post<VolumeProfileResponse>('/api/analytics/volume-profile', request);
  }

  async getCorrelationMatrix(instrumentIds: number[], timeframe?: string): Promise<CorrelationMatrixResponse> {
    return this.post<CorrelationMatrixResponse>('/api/analytics/correlation-matrix', {
      instrumentIds,
      timeframe
    });
  }

  async getMarketMicrostructure(instrumentId: number): Promise<MarketMicrostructureResponse> {
    return this.post<MarketMicrostructureResponse>('/api/analytics/market-microstructure', {
      instrumentId
    });
  }

  // Analytics health check
  async getAnalyticsHealth(): Promise<{ status: string; services: Record<string, any> }> {
    return this.get('/api/analytics/health');
  }

  // =============================================================================
  // UTILITY METHODS
  // =============================================================================

  private serializeParams(params: Record<string, any>): Record<string, string> {
    const serialized: Record<string, string> = {};
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        serialized[key] = String(value);
      }
    });

    return serialized;
  }

  // Update base URL (useful for environment switching)
  setBaseUrl(baseUrl: string): void {
    this.baseUrl = baseUrl;
  }

  // Add authentication header
  setAuthToken(token: string): void {
    this.defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  // Remove authentication header
  clearAuthToken(): void {
    delete this.defaultHeaders['Authorization'];
  }

  // Set demo mode
  setDemoMode(enabled: boolean): void {
    if (enabled) {
      this.defaultHeaders['X-Demo-Mode'] = 'true';
    } else {
      delete this.defaultHeaders['X-Demo-Mode'];
    }
  }

  // =============================================================================
  // AUTHENTICATION API
  // =============================================================================

  async initiateOAuth(): Promise<{
    authorization_url: string;
    state: string;
    expires_at: string;
    demo_mode: boolean;
  }> {
    return this.post('/api/auth/oauth/initiate');
  }

  async completeOAuth(code: string, state: string): Promise<{
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
    scope: string;
    user_info: any;
    demo_mode: boolean;
  }> {
    return this.post('/api/auth/oauth/complete', {
      code,
      state
    });
  }

  async refreshToken(refreshToken?: string): Promise<{
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
    scope: string;
    user_info: any;
    demo_mode: boolean;
  }> {
    // If no refresh token provided, try to get it from storage
    const tokenToUse = refreshToken || sessionStorage.getItem('refresh_token');
    
    if (!tokenToUse) {
      throw new ApiError(401, 'No refresh token available', null);
    }

    return this.post('/api/auth/token/refresh', {
      refresh_token: tokenToUse
    });
  }

  async getAuthStatus(): Promise<{
    is_authenticated: boolean;
    user_info?: any;
    token_expires_at?: string;
    demo_mode: boolean;
    connection_status: string;
  }> {
    return this.get('/api/auth/status');
  }

  async logout(): Promise<{
    success: boolean;
    message: string;
  }> {
    return this.post('/api/auth/logout');
  }
}

// =============================================================================
// ERROR HANDLING
// =============================================================================

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data: any = null
  ) {
    super(message);
    this.name = 'ApiError';
  }

  get isNetworkError(): boolean {
    return this.status === 0;
  }

  get isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  get isServerError(): boolean {
    return this.status >= 500;
  }

  get isValidationError(): boolean {
    return this.status === 422;
  }

  get isNotFoundError(): boolean {
    return this.status === 404;
  }

  get isUnauthorizedError(): boolean {
    return this.status === 401;
  }

  get isForbiddenError(): boolean {
    return this.status === 403;
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

export const apiClient = new ApiClient();

// =============================================================================
// REACT QUERY INTEGRATION HELPERS
// =============================================================================

/**
 * Query key factory for consistent cache keys
 */
export const queryKeys = {
  // Health
  health: () => ['health'] as const,
  healthDetailed: () => ['health', 'detailed'] as const,

  // Instruments
  instruments: (filters?: InstrumentFilters) => ['instruments', filters] as const,
  instrument: (id: number) => ['instruments', id] as const,

  // Alert Rules
  alertRules: (filters?: AlertRuleFilters) => ['alertRules', filters] as const,
  alertRule: (id: number) => ['alertRules', id] as const,

  // Alerts
  alerts: (filters?: AlertLogFilters, pagination?: PaginationParams) => 
    ['alerts', filters, pagination] as const,
  alertStats: () => ['alerts', 'stats'] as const,

  // Analytics
  analytics: {
    health: () => ['analytics', 'health'] as const,
    marketAnalysis: (request: AnalyticsRequest) => ['analytics', 'market-analysis', request] as const,
    realTimeIndicators: (request: AnalyticsRequest) => ['analytics', 'real-time-indicators', request] as const,
    pricePrediction: (request: PredictionRequest) => ['analytics', 'price-prediction', request] as const,
    anomalyDetection: (request: AnalyticsRequest) => ['analytics', 'anomaly-detection', request] as const,
    trendClassification: (request: AnalyticsRequest) => ['analytics', 'trend-classification', request] as const,
    varCalculation: (request: RiskRequest) => ['analytics', 'var-calculation', request] as const,
    riskMetrics: (request: RiskRequest) => ['analytics', 'risk-metrics', request] as const,
    stressTest: (request: StressTestRequest) => ['analytics', 'stress-test', request] as const,
    volumeProfile: (request: VolumeProfileRequest) => ['analytics', 'volume-profile', request] as const,
    correlationMatrix: (instrumentIds: number[], timeframe?: string) => 
      ['analytics', 'correlation-matrix', instrumentIds, timeframe] as const,
    marketMicrostructure: (instrumentId: number) => ['analytics', 'market-microstructure', instrumentId] as const,
  }
};

/**
 * Mutation options factory for consistent cache invalidation
 */
export const mutationOptions = {
  instrument: {
    onSuccess: () => {
      // Invalidate instruments queries - handled by React Query in components
    }
  },
  alertRule: {
    onSuccess: () => {
      // Invalidate alert rules queries - handled by React Query in components
    }
  },
  alert: {
    onSuccess: () => {
      // Invalidate alerts queries - handled by React Query in components
    }
  }
};