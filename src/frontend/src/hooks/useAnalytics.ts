/**
 * Analytics hooks for TradeAssist Frontend
 * 
 * Provides React Query-based hooks for all analytics endpoints with proper
 * error handling, caching strategies, and loading states.
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { apiClient, queryKeys } from '../services/apiClient';
import { 
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

// =============================================================================
// ANALYTICS DATA TYPES
// =============================================================================

export type AnalyticsDataType = 
  | 'market-analysis'
  | 'real-time-indicators'  
  | 'price-prediction'
  | 'risk-metrics'
  | 'anomaly-detection'
  | 'trend-classification'
  | 'var-calculation'
  | 'stress-test'
  | 'volume-profile'
  | 'correlation-matrix'
  | 'market-microstructure';

export interface AnalyticsHookOptions {
  enabled?: boolean;
  refetchInterval?: number;
  staleTime?: number;
  retry?: boolean | number;
}

// =============================================================================
// GENERIC ANALYTICS HOOK
// =============================================================================

/**
 * Generic analytics hook that supports all analytics endpoint types
 */
export function useAnalytics<T = any>(
  type: AnalyticsDataType,
  request: AnalyticsRequest | PredictionRequest | RiskRequest | StressTestRequest | VolumeProfileRequest,
  options: AnalyticsHookOptions = {}
): UseQueryResult<T> {
  return useQuery({
    queryKey: getAnalyticsQueryKey(type, request),
    queryFn: async () => {
      switch (type) {
        case 'market-analysis':
          return apiClient.getMarketAnalysis(request as AnalyticsRequest);
        case 'real-time-indicators':
          return apiClient.getRealTimeIndicators(request as AnalyticsRequest);
        case 'price-prediction':
          return apiClient.predictPrice(request as PredictionRequest);
        case 'risk-metrics':
          return apiClient.getRiskMetrics(request as RiskRequest);
        case 'anomaly-detection':
          return apiClient.detectAnomalies(request as AnalyticsRequest);
        case 'trend-classification':
          return apiClient.classifyTrend(request as AnalyticsRequest);
        case 'var-calculation':
          return apiClient.calculateVar(request as RiskRequest);
        case 'stress-test':
          return apiClient.performStressTest(request as StressTestRequest);
        case 'volume-profile':
          return apiClient.getVolumeProfile(request as VolumeProfileRequest);
        case 'market-microstructure':
          return apiClient.getMarketMicrostructure((request as any).instrumentId);
        default:
          throw new Error(`Unknown analytics type: ${type}`);
      }
    },
    enabled: options.enabled !== false && !!request.instrumentId,
    refetchInterval: options.refetchInterval || getDefaultRefetchInterval(type),
    staleTime: options.staleTime || getDefaultStaleTime(type),
    retry: (failureCount, error: any) => {
      // Don't retry on client errors (4xx)
      if (error?.status >= 400 && error?.status < 500) {
        return false;
      }
      
      if (typeof options.retry === 'number') {
        return failureCount < options.retry;
      }
      
      if (typeof options.retry === 'boolean') {
        return options.retry && failureCount < 3;
      }
      
      return failureCount < 3;
    },
  });
}

// =============================================================================
// SPECIALIZED ANALYTICS HOOKS
// =============================================================================

/**
 * Hook for market analysis with trend detection and technical patterns
 */
export function useMarketAnalysis(
  instrumentId: number,
  options: AnalyticsHookOptions & {
    indicators?: string[];
    includePatterns?: boolean;
    timeframe?: string;
    lookbackPeriod?: number;
  } = {}
) {
  const { indicators, includePatterns, timeframe, lookbackPeriod, ...hookOptions } = options;
  
  return useAnalytics<MarketAnalysisResponse>('market-analysis', {
    instrumentId,
    lookbackHours: lookbackPeriod,
    indicators,
  }, hookOptions);
}

/**
 * Hook for real-time technical indicators
 */
export function useRealTimeIndicators(
  instrumentId: number,
  options: AnalyticsHookOptions & {
    timeframe?: string;
    lookbackPeriod?: number;
  } = {}
) {
  const { timeframe, lookbackPeriod, ...hookOptions } = options;
  
  return useAnalytics<TechnicalIndicatorResponse>('real-time-indicators', {
    instrumentId,
    lookbackHours: lookbackPeriod
  }, {
    refetchInterval: 5000, // More frequent updates for real-time data
    ...hookOptions
  });
}

/**
 * Hook for ML-based price predictions
 */
export function usePricePrediction(
  instrumentId: number,
  predictionHorizon: number = 24,
  options: AnalyticsHookOptions & {
    modelType?: string;
    confidenceLevel?: number;
  } = {}
) {
  const { modelType, confidenceLevel, ...hookOptions } = options;
  
  return useAnalytics<PredictionResponse>('price-prediction', {
    instrumentId,
    predictionHorizon,
    modelType,
    confidenceLevel
  }, {
    staleTime: 10 * 60 * 1000, // 10 minutes - predictions update less frequently
    ...hookOptions
  });
}

/**
 * Hook for risk metrics analysis
 */
export function useRiskMetrics(
  instrumentId: number,
  options: AnalyticsHookOptions & {
    portfolioValue?: number;
    confidenceLevel?: number;
    timeframe?: string;
  } = {}
) {
  const { portfolioValue, confidenceLevel, timeframe, ...hookOptions } = options;
  
  return useAnalytics<RiskMetricsResponse>('risk-metrics', {
    instrumentId,
    portfolioValue,
    confidenceLevel,
    timeframe
  }, hookOptions);
}

/**
 * Hook for anomaly detection using statistical analysis
 */
export function useAnomalyDetection(
  instrumentId: number,
  options: AnalyticsHookOptions & {
    timeframe?: string;
    lookbackPeriod?: number;
  } = {}
) {
  const { timeframe, lookbackPeriod, ...hookOptions } = options;
  
  return useAnalytics<AnomalyDetectionResponse>('anomaly-detection', {
    instrumentId,
    timeframe,
    lookbackPeriod
  }, hookOptions);
}

/**
 * Hook for trend classification using pattern recognition
 */
export function useTrendClassification(
  instrumentId: number,
  options: AnalyticsHookOptions & {
    timeframe?: string;
    lookbackPeriod?: number;
  } = {}
) {
  const { timeframe, lookbackPeriod, ...hookOptions } = options;
  
  return useAnalytics<TrendClassificationResponse>('trend-classification', {
    instrumentId,
    timeframe,
    lookbackPeriod
  }, hookOptions);
}

/**
 * Hook for Value at Risk (VaR) calculations
 */
export function useVarCalculation(
  instrumentId: number,
  options: AnalyticsHookOptions & {
    portfolioValue?: number;
    confidenceLevel?: number;
    timeframe?: string;
  } = {}
) {
  const { portfolioValue, confidenceLevel, timeframe, ...hookOptions } = options;
  
  return useAnalytics<VarCalculationResponse>('var-calculation', {
    instrumentId,
    portfolioValue,
    confidenceLevel,
    timeframe
  }, hookOptions);
}

/**
 * Hook for portfolio stress testing
 */
export function useStressTest(
  instrumentId: number,
  scenarios: Array<{ name: string; marketShock: number; duration: number }> = [],
  options: AnalyticsHookOptions & {
    portfolioValue?: number;
    timeframe?: string;
  } = {}
) {
  const { portfolioValue, timeframe, ...hookOptions } = options;
  
  return useAnalytics<StressTestResponse>('stress-test', {
    instrumentId,
    portfolioValue,
    timeframe,
    scenarios
  }, hookOptions);
}

/**
 * Hook for volume profile analysis
 */
export function useVolumeProfile(
  instrumentId: number,
  options: AnalyticsHookOptions & {
    timeframe?: string;
    priceSegments?: number;
    includePointOfControl?: boolean;
  } = {}
) {
  const { timeframe, priceSegments, includePointOfControl, ...hookOptions } = options;
  
  return useAnalytics<VolumeProfileResponse>('volume-profile', {
    instrumentId,
    timeframe,
    priceSegments,
    includePointOfControl
  }, hookOptions);
}

/**
 * Hook for correlation matrix between instruments
 */
export function useCorrelationMatrix(
  instrumentIds: number[],
  options: AnalyticsHookOptions & {
    timeframe?: string;
    lookbackPeriod?: number;
  } = {}
) {
  const { timeframe, lookbackPeriod, ...hookOptions } = options;
  
  return useQuery({
    queryKey: queryKeys.analytics.correlationMatrix(instrumentIds, timeframe),
    queryFn: () => apiClient.getCorrelationMatrix(instrumentIds, timeframe),
    enabled: hookOptions.enabled !== false && instrumentIds.length > 1,
    refetchInterval: hookOptions.refetchInterval || 60000, // 1 minute
    staleTime: hookOptions.staleTime || 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error: any) => {
      if (error?.status >= 400 && error?.status < 500) {
        return false;
      }
      return failureCount < 3;
    }
  }) as UseQueryResult<CorrelationMatrixResponse>;
}

/**
 * Hook for market microstructure analysis
 */
export function useMarketMicrostructure(
  instrumentId: number,
  options: AnalyticsHookOptions = {}
) {
  return useAnalytics<MarketMicrostructureResponse>('market-microstructure', {
    instrumentId
  }, {
    refetchInterval: 10000, // 10 seconds for microstructure data
    ...options
  });
}

// =============================================================================
// BATCH ANALYTICS HOOKS
// =============================================================================

/**
 * Hook for comprehensive analytics data for a single instrument
 */
export function useComprehensiveAnalytics(
  instrumentId: number,
  options: AnalyticsHookOptions = {}
) {
  const marketAnalysis = useMarketAnalysis(instrumentId, options);
  const realTimeIndicators = useRealTimeIndicators(instrumentId, options);
  const pricePrediction = usePricePrediction(instrumentId, 24, options);
  const riskMetrics = useRiskMetrics(instrumentId, options);
  const anomalyDetection = useAnomalyDetection(instrumentId, options);
  const trendClassification = useTrendClassification(instrumentId, options);

  return {
    marketAnalysis,
    realTimeIndicators,
    pricePrediction,
    riskMetrics,
    anomalyDetection,
    trendClassification,
    isLoading: marketAnalysis.isLoading || realTimeIndicators.isLoading || 
               pricePrediction.isLoading || riskMetrics.isLoading ||
               anomalyDetection.isLoading || trendClassification.isLoading,
    hasError: marketAnalysis.error || realTimeIndicators.error || 
              pricePrediction.error || riskMetrics.error ||
              anomalyDetection.error || trendClassification.error,
  };
}

/**
 * Hook for multiple instruments basic analytics
 * Note: For React Hooks compliance, this should be used with a consistent number of instruments
 * For dynamic instrument lists, consider using separate hooks or the correlation matrix hook
 */
export function useMultiInstrumentAnalytics(
  instrumentIds: number[],
  options: AnalyticsHookOptions = {}
) {
  // Use correlation matrix hook which handles multiple instruments properly
  // and can provide individual instrument analytics as well
  const correlationData = useCorrelationMatrix(instrumentIds, options);
  
  // For now, disable this hook and recommend using individual hooks
  // This prevents the React Hooks rules violation
  console.warn('useMultiInstrumentAnalytics is deprecated. Use individual analytics hooks for each instrument or useCorrelationMatrix for multi-instrument analysis.');
  
  return {
    results: [],
    isLoading: false,
    hasError: false,
    deprecated: true,
    alternativeData: correlationData
  };
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function getAnalyticsQueryKey(type: AnalyticsDataType, request: any): readonly any[] {
  switch (type) {
    case 'market-analysis':
      return queryKeys.analytics.marketAnalysis(request);
    case 'real-time-indicators':
      return queryKeys.analytics.realTimeIndicators(request);
    case 'price-prediction':
      return queryKeys.analytics.pricePrediction(request);
    case 'risk-metrics':
      return queryKeys.analytics.riskMetrics(request);
    case 'anomaly-detection':
      return queryKeys.analytics.anomalyDetection(request);
    case 'trend-classification':
      return queryKeys.analytics.trendClassification(request);
    case 'var-calculation':
      return queryKeys.analytics.varCalculation(request);
    case 'stress-test':
      return queryKeys.analytics.stressTest(request);
    case 'volume-profile':
      return queryKeys.analytics.volumeProfile(request);
    case 'market-microstructure':
      return queryKeys.analytics.marketMicrostructure(request.instrumentId);
    default:
      return ['analytics', type, request];
  }
}

function getDefaultRefetchInterval(type: AnalyticsDataType): number {
  switch (type) {
    case 'real-time-indicators':
    case 'market-microstructure':
      return 5000; // 5 seconds for real-time data
    case 'market-analysis':
    case 'anomaly-detection':
      return 30000; // 30 seconds for analysis data
    case 'price-prediction':
    case 'trend-classification':
      return 60000; // 1 minute for predictions
    case 'risk-metrics':
    case 'var-calculation':
    case 'volume-profile':
      return 120000; // 2 minutes for risk/volume data
    case 'stress-test':
    case 'correlation-matrix':
      return 300000; // 5 minutes for heavy computations
    default:
      return 30000; // 30 seconds default
  }
}

function getDefaultStaleTime(type: AnalyticsDataType): number {
  switch (type) {
    case 'real-time-indicators':
    case 'market-microstructure':
      return 30000; // 30 seconds for real-time data
    case 'market-analysis':
    case 'anomaly-detection':
      return 2 * 60 * 1000; // 2 minutes for analysis
    case 'price-prediction':
    case 'trend-classification':
      return 5 * 60 * 1000; // 5 minutes for predictions
    case 'risk-metrics':
    case 'var-calculation':
    case 'volume-profile':
      return 10 * 60 * 1000; // 10 minutes for risk/volume
    case 'stress-test':
    case 'correlation-matrix':
      return 15 * 60 * 1000; // 15 minutes for heavy computations
    default:
      return 5 * 60 * 1000; // 5 minutes default
  }
}

// =============================================================================
// ANALYTICS HEALTH HOOK
// =============================================================================

/**
 * Hook for analytics service health monitoring
 */
export function useAnalyticsHealth(options: AnalyticsHookOptions = {}) {
  return useQuery({
    queryKey: queryKeys.analytics.health(),
    queryFn: () => apiClient.getAnalyticsHealth(),
    enabled: options.enabled !== false,
    refetchInterval: options.refetchInterval || 30000, // 30 seconds
    staleTime: options.staleTime || 60 * 1000, // 1 minute
    retry: 2
  });
}

// =============================================================================
// TYPE EXPORTS
// =============================================================================

export type {
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
  MarketMicrostructureResponse,
};