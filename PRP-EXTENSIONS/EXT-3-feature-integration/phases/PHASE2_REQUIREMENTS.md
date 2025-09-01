# Phase 2: Analytics API Integration & Frontend Components

## Phase Overview
- **Phase Name**: Analytics API Integration & Frontend Components
- **Phase Number**: 2 of 4  
- **Estimated Duration**: 6-8 days
- **Implementation Effort**: 30% of total extension
- **Primary Focus**: Make all 11 backend analytics endpoints accessible through frontend UI

## Phase Objectives

### Primary Goals
1. **Complete Analytics API Integration**: Extend API client with all 11 analytics endpoint methods
2. **Build Analytics Dashboard**: Create comprehensive frontend components for analytics display
3. **Implement Custom Hooks**: Create reusable hooks for analytics data management
4. **Add Error Handling**: Robust error handling and loading states for analytics operations
5. **Enable React Query Caching**: Optimize performance with intelligent caching and background updates

### Success Criteria
- [ ] All 11 analytics endpoints accessible through API client methods
- [ ] Analytics dashboard displays market analysis, indicators, and predictions  
- [ ] React Query integration provides caching and optimistic updates
- [ ] Error handling implemented for all analytics API operations
- [ ] Loading states implemented for all asynchronous analytics operations

## Prerequisites from Phase 1
- [x] Complete TypeScript interfaces for all analytics request/response models
- [x] Field transformation utilities (snakeToCamel/camelToSnake) functional
- [x] Type-safe API client foundation established
- [x] Zero TypeScript compilation errors in existing codebase

## Technical Requirements

### Analytics API Client Extension

#### 1. API Client Method Implementation
```typescript
// src/frontend/src/services/apiClient.ts - Analytics section extension

export class ApiClient {
  // ... existing implementation ...

  // =============================================================================
  // ANALYTICS API - NEW IMPLEMENTATION
  // =============================================================================

  /**
   * Get comprehensive market analysis including technical indicators
   */
  async getMarketAnalysis(request: MarketAnalysisRequest): Promise<MarketAnalysisResponse> {
    const transformedRequest = this.transformRequest(request);
    return this.post<MarketAnalysisResponse>('/api/analytics/market-analysis', transformedRequest);
  }

  /**
   * Get real-time technical indicators for specified instrument
   */
  async getRealTimeIndicators(request: AnalyticsRequest): Promise<TechnicalIndicatorResponse> {
    const transformedRequest = this.transformRequest(request);
    return this.post<TechnicalIndicatorResponse>('/api/analytics/real-time-indicators', transformedRequest);
  }

  /**
   * Get ML-based price predictions
   */
  async predictPrice(request: PredictionRequest): Promise<PredictionResponse> {
    const transformedRequest = this.transformRequest(request);
    return this.post<PredictionResponse>('/api/analytics/price-prediction', transformedRequest);
  }

  /**
   * Detect market anomalies using statistical analysis
   */
  async detectAnomalies(request: AnalyticsRequest): Promise<AnomalyDetectionResponse> {
    const transformedRequest = this.transformRequest(request);
    return this.post<AnomalyDetectionResponse>('/api/analytics/anomaly-detection', transformedRequest);
  }

  /**
   * Classify market trends using pattern recognition
   */
  async classifyTrend(request: AnalyticsRequest): Promise<TrendClassificationResponse> {
    const transformedRequest = this.transformRequest(request);
    return this.post<TrendClassificationResponse>('/api/analytics/trend-classification', transformedRequest);
  }

  /**
   * Calculate Value at Risk (VaR) for risk management
   */
  async calculateVaR(request: RiskRequest): Promise<VaRCalculationResponse> {
    const transformedRequest = this.transformRequest(request);
    return this.post<VaRCalculationResponse>('/api/analytics/var-calculation', transformedRequest);
  }

  /**
   * Get comprehensive risk metrics analysis
   */
  async getRiskMetrics(request: RiskRequest): Promise<RiskMetricsResponse> {
    const transformedRequest = this.transformRequest(request);
    return this.post<RiskMetricsResponse>('/api/analytics/risk-metrics', transformedRequest);
  }

  /**
   * Perform portfolio stress testing scenarios
   */
  async performStressTest(request: StressTestRequest): Promise<StressTestResponse> {
    const transformedRequest = this.transformRequest(request);
    return this.post<StressTestResponse>('/api/analytics/stress-test', transformedRequest);
  }

  /**
   * Get volume profile analysis for market structure understanding
   */
  async getVolumeProfile(request: VolumeProfileRequest): Promise<VolumeProfileResponse> {
    const transformedRequest = this.transformRequest(request);
    return this.post<VolumeProfileResponse>('/api/analytics/volume-profile', transformedRequest);
  }

  /**
   * Calculate correlation matrix for asset relationship analysis
   */
  async getCorrelationMatrix(request: CorrelationRequest): Promise<CorrelationMatrixResponse> {
    const transformedRequest = this.transformRequest(request);
    return this.post<CorrelationMatrixResponse>('/api/analytics/correlation-matrix', transformedRequest);
  }

  /**
   * Get market microstructure metrics for advanced analysis
   */
  async getMarketMicrostructure(request: AnalyticsRequest): Promise<MicrostructureResponse> {
    const transformedRequest = this.transformRequest(request);
    return this.post<MicrostructureResponse>('/api/analytics/market-microstructure', transformedRequest);
  }
}
```

#### 2. Enhanced Type Definitions
```typescript
// src/frontend/src/types/analytics.ts - Complete analytics type system

// Base request types
interface AnalyticsRequest {
  instrumentId: number;
  timeframe?: 'minute' | 'hour' | 'day' | 'week';
  lookbackPeriod?: number;
  parameters?: Record<string, any>;
}

interface MarketAnalysisRequest extends AnalyticsRequest {
  indicators?: string[]; // ['RSI', 'MACD', 'BOLLINGER_BANDS']
  includePatterns?: boolean;
}

interface PredictionRequest extends AnalyticsRequest {
  predictionHorizon: number; // hours
  modelType?: 'linear' | 'lstm' | 'ensemble';
  confidenceLevel?: number;
}

interface RiskRequest extends AnalyticsRequest {
  portfolioValue?: number;
  confidenceLevel?: number; // 0.95, 0.99
}

interface StressTestRequest extends RiskRequest {
  scenarios?: Array<{
    name: string;
    marketShock: number; // percentage change
    duration: number; // days
  }>;
}

interface VolumeProfileRequest extends AnalyticsRequest {
  priceSegments?: number;
  includePointOfControl?: boolean;
}

interface CorrelationRequest {
  instrumentIds: number[];
  timeframe: 'minute' | 'hour' | 'day';
  lookbackPeriod: number;
}

// Response types
interface MarketAnalysisResponse {
  instrumentId: number;
  analysis: {
    trend: 'bullish' | 'bearish' | 'neutral';
    strength: number; // 0-1
    support: number[];
    resistance: number[];
  };
  indicators: {
    rsi?: {
      value: number;
      signal: 'overbought' | 'oversold' | 'neutral';
    };
    macd?: {
      macd: number;
      signal: number;
      histogram: number;
      trend: 'bullish' | 'bearish';
    };
    bollingerBands?: {
      upper: number;
      middle: number;
      lower: number;
      position: 'above' | 'below' | 'between';
    };
  };
  patterns?: Array<{
    name: string;
    confidence: number;
    timeframe: string;
  }>;
  timestamp: string;
}

interface TechnicalIndicatorResponse {
  instrumentId: number;
  indicators: {
    [key: string]: any; // Flexible for various indicator types
  };
  calculatedAt: string;
  nextUpdate?: string;
}

interface PredictionResponse {
  instrumentId: number;
  predictions: Array<{
    timestamp: string;
    predictedPrice: number;
    confidenceInterval: {
      lower: number;
      upper: number;
    };
  }>;
  modelMetrics: {
    modelType: string;
    accuracy: number;
    mse: number;
  };
  generatedAt: string;
}

interface RiskMetricsResponse {
  instrumentId: number;
  metrics: {
    var95: number;
    var99: number;
    expectedShortfall: number;
    maxDrawdown: number;
    sharpeRatio: number;
    volatility: number;
  };
  calculatedAt: string;
}
```

### Custom Hooks Implementation

#### 1. Analytics Data Hooks
```typescript
// src/frontend/src/hooks/useAnalytics.ts

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { 
  AnalyticsRequest,
  MarketAnalysisResponse,
  TechnicalIndicatorResponse,
  PredictionResponse,
  RiskMetricsResponse
} from '../types/analytics';

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

/**
 * Generic analytics hook that supports all analytics endpoint types
 */
export function useAnalytics<T = any>(
  type: AnalyticsDataType,
  request: AnalyticsRequest | PredictionRequest | RiskRequest,
  options?: {
    enabled?: boolean;
    refetchInterval?: number;
    staleTime?: number;
  }
): UseQueryResult<T> {
  return useQuery({
    queryKey: ['analytics', type, request],
    queryFn: async () => {
      switch (type) {
        case 'market-analysis':
          return apiClient.getMarketAnalysis(request as MarketAnalysisRequest);
        case 'real-time-indicators':
          return apiClient.getRealTimeIndicators(request);
        case 'price-prediction':
          return apiClient.predictPrice(request as PredictionRequest);
        case 'risk-metrics':
          return apiClient.getRiskMetrics(request as RiskRequest);
        case 'anomaly-detection':
          return apiClient.detectAnomalies(request);
        case 'trend-classification':
          return apiClient.classifyTrend(request);
        case 'var-calculation':
          return apiClient.calculateVaR(request as RiskRequest);
        case 'stress-test':
          return apiClient.performStressTest(request as StressTestRequest);
        case 'volume-profile':
          return apiClient.getVolumeProfile(request as VolumeProfileRequest);
        case 'correlation-matrix':
          return apiClient.getCorrelationMatrix(request as CorrelationRequest);
        case 'market-microstructure':
          return apiClient.getMarketMicrostructure(request);
        default:
          throw new Error(`Unknown analytics type: ${type}`);
      }
    },
    enabled: options?.enabled !== false,
    refetchInterval: options?.refetchInterval || 30000, // 30 seconds default
    staleTime: options?.staleTime || 5 * 60 * 1000, // 5 minutes default
    retry: (failureCount, error: any) => {
      // Don't retry on client errors (4xx)
      if (error?.status >= 400 && error?.status < 500) {
        return false;
      }
      return failureCount < 3;
    },
  });
}

/**
 * Specialized hook for market analysis
 */
export function useMarketAnalysis(
  instrumentId: number,
  options?: { indicators?: string[]; includePatterns?: boolean }
) {
  return useAnalytics<MarketAnalysisResponse>('market-analysis', {
    instrumentId,
    ...options,
  });
}

/**
 * Specialized hook for real-time indicators
 */
export function useRealTimeIndicators(instrumentId: number) {
  return useAnalytics<TechnicalIndicatorResponse>('real-time-indicators', {
    instrumentId,
  }, {
    refetchInterval: 5000, // More frequent updates for real-time data
  });
}

/**
 * Specialized hook for price predictions
 */
export function usePricePrediction(
  instrumentId: number, 
  predictionHorizon: number = 24
) {
  return useAnalytics<PredictionResponse>('price-prediction', {
    instrumentId,
    predictionHorizon,
  }, {
    staleTime: 10 * 60 * 1000, // 10 minutes - predictions update less frequently
  });
}

/**
 * Specialized hook for risk metrics
 */
export function useRiskMetrics(instrumentId: number, portfolioValue?: number) {
  return useAnalytics<RiskMetricsResponse>('risk-metrics', {
    instrumentId,
    portfolioValue,
  });
}
```

### Frontend Component Architecture

#### 1. Analytics Dashboard Container
```typescript
// src/frontend/src/components/Analytics/AnalyticsDashboard.tsx

import React, { useState } from 'react';
import { Grid, Paper, Typography, Alert, Skeleton } from '@mui/material';
import { InstrumentSelector } from '../common/InstrumentSelector';
import { MarketAnalysisSection } from './MarketAnalysisSection';
import { TechnicalIndicatorsSection } from './TechnicalIndicatorsSection';
import { PricePredictionSection } from './PricePredictionSection';
import { RiskMetricsSection } from './RiskMetricsSection';
import { VolumeProfileSection } from './VolumeProfileSection';

interface AnalyticsDashboardProps {
  defaultInstrumentId?: number;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  defaultInstrumentId = 1
}) => {
  const [selectedInstrumentId, setSelectedInstrumentId] = useState(defaultInstrumentId);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');

  return (
    <div className="analytics-dashboard">
      <Typography variant="h4" gutterBottom>
        Analytics Dashboard
      </Typography>
      
      <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
        <InstrumentSelector
          value={selectedInstrumentId}
          onChange={(instrumentId, symbol) => {
            setSelectedInstrumentId(instrumentId);
            setSelectedSymbol(symbol);
          }}
        />
      </Paper>

      <Grid container spacing={3}>
        {/* Market Analysis Section */}
        <Grid item xs={12} lg={6}>
          <MarketAnalysisSection 
            instrumentId={selectedInstrumentId}
            symbol={selectedSymbol}
          />
        </Grid>

        {/* Technical Indicators Section */}
        <Grid item xs={12} lg={6}>
          <TechnicalIndicatorsSection 
            instrumentId={selectedInstrumentId}
            symbol={selectedSymbol}
          />
        </Grid>

        {/* Price Prediction Section */}
        <Grid item xs={12} lg={8}>
          <PricePredictionSection 
            instrumentId={selectedInstrumentId}
            symbol={selectedSymbol}
          />
        </Grid>

        {/* Risk Metrics Section */}
        <Grid item xs={12} lg={4}>
          <RiskMetricsSection 
            instrumentId={selectedInstrumentId}
            symbol={selectedSymbol}
          />
        </Grid>

        {/* Volume Profile Section */}
        <Grid item xs={12}>
          <VolumeProfileSection 
            instrumentId={selectedInstrumentId}
            symbol={selectedSymbol}
          />
        </Grid>
      </Grid>
    </div>
  );
};
```

#### 2. Market Analysis Component  
```typescript
// src/frontend/src/components/Analytics/MarketAnalysisSection.tsx

import React from 'react';
import { Paper, Typography, Box, Chip, Alert, Skeleton } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat } from '@mui/icons-material';
import { useMarketAnalysis } from '../../hooks/useAnalytics';

interface MarketAnalysisSectionProps {
  instrumentId: number;
  symbol: string;
}

export const MarketAnalysisSection: React.FC<MarketAnalysisSectionProps> = ({
  instrumentId,
  symbol
}) => {
  const { data: analysis, isLoading, error } = useMarketAnalysis(instrumentId, {
    indicators: ['RSI', 'MACD', 'BOLLINGER_BANDS'],
    includePatterns: true
  });

  if (error) {
    return (
      <Paper elevation={2} sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Market Analysis</Typography>
        <Alert severity="error">
          Failed to load market analysis: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
      </Paper>
    );
  }

  if (isLoading) {
    return (
      <Paper elevation={2} sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Market Analysis</Typography>
        <Skeleton variant="rectangular" height={200} />
      </Paper>
    );
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'bullish':
        return <TrendingUp color="success" />;
      case 'bearish':
        return <TrendingDown color="error" />;
      default:
        return <TrendingFlat color="action" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'bullish':
        return 'success';
      case 'bearish':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Paper elevation={2} sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Market Analysis - {symbol}
      </Typography>
      
      {analysis && (
        <Box>
          {/* Overall Trend */}
          <Box display="flex" alignItems="center" mb={2}>
            {getTrendIcon(analysis.analysis.trend)}
            <Chip
              label={`${analysis.analysis.trend.toUpperCase()} (${(analysis.analysis.strength * 100).toFixed(1)}%)`}
              color={getTrendColor(analysis.analysis.trend) as any}
              sx={{ ml: 1 }}
            />
          </Box>

          {/* Support and Resistance Levels */}
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Support Levels: {analysis.analysis.support.map(level => level.toFixed(2)).join(', ')}
            </Typography>
            <Typography variant="subtitle2" gutterBottom>
              Resistance Levels: {analysis.analysis.resistance.map(level => level.toFixed(2)).join(', ')}
            </Typography>
          </Box>

          {/* Technical Indicators */}
          {analysis.indicators.rsi && (
            <Box mb={1}>
              <Typography variant="body2">
                RSI: {analysis.indicators.rsi.value.toFixed(2)} ({analysis.indicators.rsi.signal})
              </Typography>
            </Box>
          )}

          {analysis.indicators.macd && (
            <Box mb={1}>
              <Typography variant="body2">
                MACD: {analysis.indicators.macd.macd.toFixed(4)} / Signal: {analysis.indicators.macd.signal.toFixed(4)} ({analysis.indicators.macd.trend})
              </Typography>
            </Box>
          )}

          {/* Detected Patterns */}
          {analysis.patterns && analysis.patterns.length > 0 && (
            <Box mt={2}>
              <Typography variant="subtitle2" gutterBottom>Detected Patterns:</Typography>
              {analysis.patterns.map((pattern, index) => (
                <Chip
                  key={index}
                  label={`${pattern.name} (${(pattern.confidence * 100).toFixed(1)}%)`}
                  size="small"
                  sx={{ mr: 1, mb: 1 }}
                />
              ))}
            </Box>
          )}

          <Typography variant="caption" color="text.secondary">
            Last updated: {new Date(analysis.timestamp).toLocaleTimeString()}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};
```

#### 3. Technical Indicators Component
```typescript
// src/frontend/src/components/Analytics/TechnicalIndicatorsSection.tsx

import React from 'react';
import { Paper, Typography, Box, LinearProgress, Alert, Skeleton } from '@mui/material';
import { useRealTimeIndicators } from '../../hooks/useAnalytics';

interface TechnicalIndicatorsSectionProps {
  instrumentId: number;
  symbol: string;
}

export const TechnicalIndicatorsSection: React.FC<TechnicalIndicatorsSectionProps> = ({
  instrumentId,
  symbol
}) => {
  const { data: indicators, isLoading, error } = useRealTimeIndicators(instrumentId);

  if (error) {
    return (
      <Paper elevation={2} sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Technical Indicators</Typography>
        <Alert severity="error">
          Failed to load technical indicators: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
      </Paper>
    );
  }

  if (isLoading) {
    return (
      <Paper elevation={2} sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Technical Indicators</Typography>
        <Skeleton variant="rectangular" height={200} />
      </Paper>
    );
  }

  return (
    <Paper elevation={2} sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Technical Indicators - {symbol}
      </Typography>
      
      {indicators && (
        <Box>
          {/* RSI Indicator */}
          {indicators.indicators.rsi && (
            <Box mb={2}>
              <Typography variant="body2" gutterBottom>
                RSI: {indicators.indicators.rsi.toFixed(2)}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={indicators.indicators.rsi}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: 
                      indicators.indicators.rsi > 70 ? '#f44336' :
                      indicators.indicators.rsi < 30 ? '#4caf50' :
                      '#2196f3'
                  }
                }}
              />
              <Typography variant="caption" color="text.secondary">
                {indicators.indicators.rsi > 70 ? 'Overbought' :
                 indicators.indicators.rsi < 30 ? 'Oversold' :
                 'Neutral'}
              </Typography>
            </Box>
          )}

          {/* MACD Indicator */}
          {indicators.indicators.macd && (
            <Box mb={2}>
              <Typography variant="body2">
                MACD: {indicators.indicators.macd.macd?.toFixed(4) || 'N/A'}
              </Typography>
              <Typography variant="body2">
                Signal: {indicators.indicators.macd.signal?.toFixed(4) || 'N/A'}
              </Typography>
              <Typography variant="body2">
                Histogram: {indicators.indicators.macd.histogram?.toFixed(4) || 'N/A'}
              </Typography>
            </Box>
          )}

          {/* Bollinger Bands */}
          {indicators.indicators.bollingerBands && (
            <Box mb={2}>
              <Typography variant="body2">
                Upper Band: {indicators.indicators.bollingerBands.upper?.toFixed(2) || 'N/A'}
              </Typography>
              <Typography variant="body2">
                Middle Band: {indicators.indicators.bollingerBands.middle?.toFixed(2) || 'N/A'}
              </Typography>
              <Typography variant="body2">
                Lower Band: {indicators.indicators.bollingerBands.lower?.toFixed(2) || 'N/A'}
              </Typography>
            </Box>
          )}

          <Typography variant="caption" color="text.secondary">
            Last updated: {new Date(indicators.calculatedAt).toLocaleTimeString()}
            {indicators.nextUpdate && ` • Next update: ${new Date(indicators.nextUpdate).toLocaleTimeString()}`}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};
```

## Implementation Tasks

### Task 1: API Client Extension (Days 1-2)
1. **Implement All 11 Analytics Methods**
   - Add each analytics endpoint method to ApiClient class
   - Ensure proper request transformation (camelCase → snake_case)
   - Ensure proper response transformation (snake_case → camelCase)
   - Add comprehensive JSDoc documentation for each method

2. **Enhance Type Safety**
   - Create complete request/response interfaces for each endpoint
   - Add runtime validation using Zod schemas where critical
   - Update existing type definitions as needed

### Task 2: Custom Hooks Development (Days 3-4)  
1. **Create Generic useAnalytics Hook**
   - Support all 11 analytics endpoint types
   - Implement React Query integration with appropriate caching strategies
   - Add error handling and retry logic

2. **Create Specialized Hooks**
   - `useMarketAnalysis`, `useRealTimeIndicators`, `usePricePrediction`, `useRiskMetrics`
   - Optimize refresh intervals based on data type (real-time vs. batch)
   - Add loading and error states management

### Task 3: Analytics Components (Days 5-6)
1. **Build Main Dashboard Container**
   - Implement AnalyticsDashboard with instrument selection
   - Create responsive grid layout for analytics sections
   - Add global error boundary for analytics features

2. **Implement Individual Analytics Sections**
   - MarketAnalysisSection with trend display and patterns
   - TechnicalIndicatorsSection with real-time indicator display
   - PricePredictionSection with prediction charts
   - RiskMetricsSection with risk analysis display
   - VolumeProfileSection with volume analysis

### Task 4: Integration & Testing (Days 7-8)
1. **Component Integration**
   - Integrate analytics dashboard into main application routing
   - Add navigation links to analytics features
   - Test component interactions and data flow

2. **Error Handling Enhancement**  
   - Implement comprehensive error boundaries
   - Add user-friendly error messages for each analytics operation
   - Test error scenarios and recovery mechanisms

3. **Performance Optimization**
   - Implement React Query caching strategies
   - Add loading skeletons and optimistic updates
   - Test component performance with real data

## Phase 2 Dependencies

### Requires from Phase 1
- [x] Complete TypeScript interfaces for analytics models
- [x] Field transformation utilities functional
- [x] Type-safe API client foundation

### Provides to Phase 3  
- Complete analytics dashboard with all 11 endpoints functional
- Analytics data hooks available for real-time integration
- Component architecture ready for WebSocket integration

## Testing Requirements

### Unit Tests
```typescript
describe('Analytics API Client', () => {
  test('getMarketAnalysis transforms request and response correctly', async () => {
    // Mock backend response with snake_case
    const mockResponse = { 
      instrument_id: 1, 
      analysis: { trend: 'bullish' },
      timestamp: '2024-01-01T10:00:00Z'
    };
    
    // Expect camelCase response
    const result = await apiClient.getMarketAnalysis({ instrumentId: 1 });
    expect(result.instrumentId).toBe(1);
    expect(result.analysis.trend).toBe('bullish');
  });
});

describe('Analytics Hooks', () => {
  test('useMarketAnalysis provides data, loading, and error states', () => {
    const { result } = renderHook(() => useMarketAnalysis(1));
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});
```

### Component Tests
```typescript
describe('MarketAnalysisSection', () => {
  test('displays market analysis data correctly', () => {
    const mockAnalysis = {
      analysis: { trend: 'bullish', strength: 0.85 },
      indicators: { rsi: { value: 65, signal: 'neutral' } }
    };
    
    render(<MarketAnalysisSection instrumentId={1} symbol="AAPL" />);
    expect(screen.getByText(/Market Analysis/)).toBeInTheDocument();
  });

  test('displays error state when API call fails', () => {
    // Mock API error
    render(<MarketAnalysisSection instrumentId={1} symbol="AAPL" />);
    expect(screen.getByText(/Failed to load/)).toBeInTheDocument();
  });
});
```

## Phase 2 Completion Criteria

### Functional Completion
- [ ] All 11 analytics endpoints accessible through frontend API client
- [ ] Analytics dashboard displays data from all endpoint types
- [ ] Custom hooks provide proper data management with React Query
- [ ] Error handling implemented for all analytics operations
- [ ] Loading states provide good user experience during API calls

### Technical Validation
- [ ] All API client methods properly typed and tested
- [ ] React Query caching working effectively for analytics data
- [ ] Components handle loading, error, and success states correctly
- [ ] Field transformation working correctly for all analytics responses
- [ ] Performance targets met for analytics dashboard rendering

### Integration Readiness
- [ ] Analytics components ready for real-time data integration in Phase 3
- [ ] Data structures prepared for WebSocket message handling
- [ ] Component architecture scalable for additional analytics features

**Phase 2 Success Metric**: Complete analytics functionality accessible through polished UI + All 11 backend endpoints functional in frontend + Foundation ready for real-time enhancements