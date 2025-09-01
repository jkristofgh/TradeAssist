/**
 * Real-Time Analytics Integration Hook
 * 
 * Integrates WebSocket real-time analytics updates with cached analytics data
 * for seamless real-time dashboard experience with <50ms update performance.
 */

import { useEffect, useState, useCallback, useMemo } from 'react';
import { useWebSocket } from '../context/WebSocketContext';
import { 
  AnalyticsUpdate, 
  TechnicalIndicatorUpdate, 
  PricePredictionUpdate, 
  RiskMetricsUpdate,
  MarketDataUpdate 
} from '../types/websocket';

// =============================================================================
// TYPES AND INTERFACES
// =============================================================================

interface RealTimeAnalyticsData {
  marketAnalysis: Record<number, AnalyticsUpdate>;
  technicalIndicators: Record<number, TechnicalIndicatorUpdate>;
  pricePredictions: Record<number, PricePredictionUpdate>;
  riskMetrics: Record<number, RiskMetricsUpdate>;
  marketData: Record<number, MarketDataUpdate>;
  lastUpdated: Record<number, string>;
  updateCount: number;
  averageUpdateLatency: number;
}

interface RealTimeAnalyticsOptions {
  autoSubscribe?: boolean;
  subscriptionTypes?: string[];
  maxHistorySize?: number;
  performanceTracking?: boolean;
}

interface InstrumentAnalytics {
  instrumentId: number;
  symbol: string;
  marketAnalysis: AnalyticsUpdate | null;
  technicalIndicators: TechnicalIndicatorUpdate | null;
  pricePrediction: PricePredictionUpdate | null;
  riskMetrics: RiskMetricsUpdate | null;
  marketData: MarketDataUpdate | null;
  lastUpdated: string | null;
  isStale: boolean;
  dataQuality: 'excellent' | 'good' | 'poor' | 'unavailable';
}

// =============================================================================
// MAIN HOOK
// =============================================================================

export const useRealTimeAnalytics = (
  instrumentIds: number[] = [],
  options: RealTimeAnalyticsOptions = {}
) => {
  const {
    autoSubscribe = true,
    subscriptionTypes = ['analytics', 'technical_indicators', 'price_prediction', 'risk_metrics', 'market_data'],
    maxHistorySize = 100,
    performanceTracking = true
  } = options;

  const { 
    isConnected, 
    subscribe, 
    unsubscribe, 
    getAnalyticsForInstrument,
    getTechnicalIndicatorsForInstrument,
    getPricePredictionForInstrument,
    getRiskMetricsForInstrument,
    realtimeData,
    analyticsData,
    technicalIndicators,
    pricePredictions,
    riskMetrics,
    performanceMetrics
  } = useWebSocket();

  const [analyticsState, setAnalyticsState] = useState<RealTimeAnalyticsData>({
    marketAnalysis: {},
    technicalIndicators: {},
    pricePredictions: {},
    riskMetrics: {},
    marketData: {},
    lastUpdated: {},
    updateCount: 0,
    averageUpdateLatency: 0
  });

  const [subscriptionHistory, setSubscriptionHistory] = useState<string[]>([]);

  // =============================================================================
  // SUBSCRIPTION MANAGEMENT
  // =============================================================================

  useEffect(() => {
    if (!isConnected || !autoSubscribe || instrumentIds.length === 0) {
      return;
    }

    const newSubscriptions: string[] = [];

    // Subscribe to each analytics type for each instrument
    instrumentIds.forEach(instrumentId => {
      subscriptionTypes.forEach(subType => {
        const subscriptionKey = `${subType}_${instrumentId}`;
        if (!subscriptionHistory.includes(subscriptionKey)) {
          subscribe(subType, instrumentId);
          newSubscriptions.push(subscriptionKey);
        }
      });
    });

    if (newSubscriptions.length > 0) {
      setSubscriptionHistory(prev => [...prev, ...newSubscriptions].slice(-maxHistorySize));
    }

    return () => {
      // Cleanup subscriptions when instrumentIds change
      newSubscriptions.forEach(subKey => {
        const [subType, instrumentIdStr] = subKey.split('_');
        unsubscribe(subType, parseInt(instrumentIdStr));
      });
    };
  }, [isConnected, instrumentIds, autoSubscribe, subscribe, unsubscribe, subscriptionTypes]);

  // =============================================================================
  // REAL-TIME DATA INTEGRATION
  // =============================================================================

  useEffect(() => {
    const startTime = performanceTracking ? performance.now() : 0;
    
    let hasUpdates = false;
    const newState = { ...analyticsState };

    // Integrate analytics data from WebSocket context
    Object.entries(analyticsData).forEach(([instrumentIdStr, data]) => {
      const instrumentId = parseInt(instrumentIdStr);
      if (instrumentIds.includes(instrumentId)) {
        newState.marketAnalysis[instrumentId] = data;
        newState.lastUpdated[instrumentId] = data.calculationTime;
        hasUpdates = true;
      }
    });

    // Integrate technical indicators
    Object.entries(technicalIndicators).forEach(([instrumentIdStr, data]) => {
      const instrumentId = parseInt(instrumentIdStr);
      if (instrumentIds.includes(instrumentId)) {
        newState.technicalIndicators[instrumentId] = data;
        newState.lastUpdated[instrumentId] = data.calculatedAt;
        hasUpdates = true;
      }
    });

    // Integrate price predictions
    Object.entries(pricePredictions).forEach(([instrumentIdStr, data]) => {
      const instrumentId = parseInt(instrumentIdStr);
      if (instrumentIds.includes(instrumentId)) {
        newState.pricePredictions[instrumentId] = data;
        newState.lastUpdated[instrumentId] = data.calculatedAt;
        hasUpdates = true;
      }
    });

    // Integrate risk metrics
    Object.entries(riskMetrics).forEach(([instrumentIdStr, data]) => {
      const instrumentId = parseInt(instrumentIdStr);
      if (instrumentIds.includes(instrumentId)) {
        newState.riskMetrics[instrumentId] = data;
        newState.lastUpdated[instrumentId] = data.calculatedAt;
        hasUpdates = true;
      }
    });

    // Integrate market data
    Object.entries(realtimeData).forEach(([instrumentIdStr, marketData]) => {
      const instrumentId = parseInt(instrumentIdStr);
      if (instrumentIds.includes(instrumentId)) {
        // Convert MarketData to MarketDataUpdate format
        const marketDataUpdate: MarketDataUpdate = {
          instrumentId: marketData.instrumentId,
          symbol: 'unknown', // Symbol not available in MarketData type
          price: marketData.price,
          volume: marketData.volume || 0,
          timestamp: marketData.timestamp,
          bid: marketData.bid || undefined,
          ask: marketData.ask || undefined,
          bidSize: marketData.bidSize || undefined,
          askSize: marketData.askSize || undefined,
          openPrice: marketData.openPrice || undefined,
          highPrice: marketData.highPrice || undefined,
          lowPrice: marketData.lowPrice || undefined
        };
        
        newState.marketData[instrumentId] = marketDataUpdate;
        newState.lastUpdated[instrumentId] = marketData.timestamp;
        hasUpdates = true;
      }
    });

    if (hasUpdates) {
      newState.updateCount = analyticsState.updateCount + 1;
      
      if (performanceTracking) {
        const processingTime = performance.now() - startTime;
        newState.averageUpdateLatency = (
          (analyticsState.averageUpdateLatency * (analyticsState.updateCount - 1)) + processingTime
        ) / analyticsState.updateCount;
        
        // Log slow updates
        if (processingTime > 50) {
          console.warn(`Slow analytics update processing: ${processingTime.toFixed(2)}ms`);
        }
      }
      
      setAnalyticsState(newState);
    }

  }, [analyticsData, technicalIndicators, pricePredictions, riskMetrics, realtimeData, instrumentIds, performanceTracking]);

  // =============================================================================
  // DATA ACCESS UTILITIES
  // =============================================================================

  const getAnalyticsForInstrument = useCallback((instrumentId: number): InstrumentAnalytics => {
    const currentTime = new Date();
    const lastUpdate = analyticsState.lastUpdated[instrumentId];
    const lastUpdateTime = lastUpdate ? new Date(lastUpdate) : null;
    
    // Determine if data is stale (older than 5 minutes)
    const isStale = lastUpdateTime ? 
      (currentTime.getTime() - lastUpdateTime.getTime()) > (5 * 60 * 1000) : true;
    
    // Determine data quality based on availability and freshness
    let dataQuality: InstrumentAnalytics['dataQuality'] = 'unavailable';
    const hasData = !!(
      analyticsState.marketAnalysis[instrumentId] ||
      analyticsState.technicalIndicators[instrumentId] ||
      analyticsState.marketData[instrumentId]
    );
    
    if (hasData && !isStale) {
      dataQuality = 'excellent';
    } else if (hasData && isStale) {
      dataQuality = 'good';
    } else if (hasData) {
      dataQuality = 'poor';
    }
    
    return {
      instrumentId,
      symbol: analyticsState.marketData[instrumentId]?.symbol || 'unknown',
      marketAnalysis: analyticsState.marketAnalysis[instrumentId] || null,
      technicalIndicators: analyticsState.technicalIndicators[instrumentId] || null,
      pricePrediction: analyticsState.pricePredictions[instrumentId] || null,
      riskMetrics: analyticsState.riskMetrics[instrumentId] || null,
      marketData: analyticsState.marketData[instrumentId] || null,
      lastUpdated: lastUpdate || null,
      isStale,
      dataQuality
    };
  }, [analyticsState]);

  const getAllInstrumentAnalytics = useCallback((): InstrumentAnalytics[] => {
    return instrumentIds.map(instrumentId => getAnalyticsForInstrument(instrumentId));
  }, [instrumentIds, getAnalyticsForInstrument]);

  const getPerformanceMetrics = useCallback(() => {
    return {
      updateCount: analyticsState.updateCount,
      averageUpdateLatency: analyticsState.averageUpdateLatency,
      websocketPerformance: performanceMetrics,
      connectionQuality: performanceMetrics.connectionQuality,
      subscriptionCount: subscriptionHistory.length,
      instrumentCount: instrumentIds.length
    };
  }, [analyticsState, performanceMetrics, subscriptionHistory, instrumentIds]);

  // =============================================================================
  // MANUAL SUBSCRIPTION CONTROLS
  // =============================================================================

  const subscribeToInstrument = useCallback((instrumentId: number, subscriptionTypes?: string[]) => {
    const types = subscriptionTypes || ['analytics', 'technical_indicators', 'market_data'];
    types.forEach(subType => {
      subscribe(subType, instrumentId);
    });
  }, [subscribe]);

  const unsubscribeFromInstrument = useCallback((instrumentId: number, subscriptionTypes?: string[]) => {
    const types = subscriptionTypes || ['analytics', 'technical_indicators', 'market_data'];
    types.forEach(subType => {
      unsubscribe(subType, instrumentId);
    });
  }, [unsubscribe]);

  // =============================================================================
  // DERIVED STATE
  // =============================================================================

  const summary = useMemo(() => {
    const totalInstruments = instrumentIds.length;
    const instrumentsWithData = instrumentIds.filter(id => 
      analyticsState.marketAnalysis[id] || 
      analyticsState.technicalIndicators[id] || 
      analyticsState.marketData[id]
    ).length;
    
    const staleInstruments = instrumentIds.filter(id => {
      const lastUpdate = analyticsState.lastUpdated[id];
      if (!lastUpdate) return true;
      return (new Date().getTime() - new Date(lastUpdate).getTime()) > (5 * 60 * 1000);
    }).length;

    return {
      totalInstruments,
      instrumentsWithData,
      dataAvailabilityRate: totalInstruments > 0 ? (instrumentsWithData / totalInstruments) * 100 : 0,
      staleInstruments,
      freshnessRate: totalInstruments > 0 ? ((totalInstruments - staleInstruments) / totalInstruments) * 100 : 0,
      averageUpdateLatency: analyticsState.averageUpdateLatency
    };
  }, [instrumentIds, analyticsState]);

  return {
    // Data access
    analyticsData: analyticsState,
    getAnalyticsForInstrument,
    getAllInstrumentAnalytics,
    
    // Performance and metrics
    getPerformanceMetrics,
    summary,
    
    // Connection status
    isConnected,
    
    // Subscription controls
    subscribeToInstrument,
    unsubscribeFromInstrument,
    
    // Raw WebSocket state for advanced usage
    rawWebSocketState: {
      realtimeData,
      analyticsData,
      technicalIndicators,
      pricePredictions,
      riskMetrics,
      performanceMetrics
    }
  };
};