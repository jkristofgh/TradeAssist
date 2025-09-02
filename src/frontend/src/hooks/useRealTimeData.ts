/**
 * Real-Time Data Management Hook
 * 
 * Provides convenient access to real-time market data, alerts, and system health
 * with optimized rendering and data management.
 */

import { useMemo, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import { 
  Instrument, 
  MarketData, 
  AlertLogWithDetails, 
  HealthStatus,
  InstrumentStatus 
} from '../types';
import { OutgoingMessage } from '../types/websocket';

// =============================================================================
// REAL-TIME DATA HOOK
// =============================================================================

export interface UseRealTimeDataOptions {
  instrumentIds?: number[];
  maxAlerts?: number;
  enableHealthMonitoring?: boolean;
}

export interface UseRealTimeDataReturn {
  // Connection state
  isConnected: boolean;
  connectionError: string | null;
  reconnectAttempts: number;
  
  // Market data
  realtimeData: Record<number, MarketData>;
  getInstrumentData: (instrumentId: number) => MarketData | null;
  getLatestPrice: (instrumentId: number) => number | null;
  
  // Alerts
  recentAlerts: AlertLogWithDetails[];
  getAlertsForInstrument: (instrumentId: number) => AlertLogWithDetails[];
  
  // System health
  systemHealth: HealthStatus | null;
  isSystemHealthy: boolean;
  
  // Actions
  connect: () => void;
  disconnect: () => void;
  sendMessage: (message: OutgoingMessage) => void;
}

export const useRealTimeData = (options: UseRealTimeDataOptions = {}): UseRealTimeDataReturn => {
  const {
    instrumentIds,
    maxAlerts = 50,
    enableHealthMonitoring = true
  } = options;

  const {
    isConnected,
    error,
    reconnectAttempts,
    realtimeData,
    recentAlerts,
    systemHealth,
    connect,
    disconnect,
    sendMessage
  } = useWebSocket();

  // =============================================================================
  // DERIVED DATA
  // =============================================================================
  
  const filteredRealtimeData = useMemo(() => {
    if (!instrumentIds?.length) {
      return realtimeData;
    }
    
    return Object.fromEntries(
      Object.entries(realtimeData).filter(([instrumentId]) => 
        instrumentIds.includes(parseInt(instrumentId, 10))
      )
    );
  }, [realtimeData, instrumentIds]);

  const limitedRecentAlerts = useMemo(() => {
    return recentAlerts.slice(0, maxAlerts);
  }, [recentAlerts, maxAlerts]);

  // =============================================================================
  // UTILITY FUNCTIONS
  // =============================================================================
  
  const getInstrumentData = useCallback((instrumentId: number): MarketData | null => {
    return realtimeData[instrumentId] || null;
  }, [realtimeData]);

  const getLatestPrice = useCallback((instrumentId: number): number | null => {
    const data = realtimeData[instrumentId];
    return data?.price || null;
  }, [realtimeData]);

  const getAlertsForInstrument = useCallback((instrumentId: number): AlertLogWithDetails[] => {
    return recentAlerts.filter(alert => alert.instrumentId === instrumentId);
  }, [recentAlerts]);

  const isSystemHealthy = useMemo(() => {
    if (!systemHealth) return false;
    
    return systemHealth.status === 'healthy' &&
           systemHealth.apiConnected &&
           systemHealth.ingestionActive;
  }, [systemHealth]);

  // =============================================================================
  // RETURN VALUE
  // =============================================================================
  
  return {
    // Connection state
    isConnected,
    connectionError: error || null,
    reconnectAttempts,
    
    // Market data
    realtimeData: filteredRealtimeData,
    getInstrumentData,
    getLatestPrice,
    
    // Alerts
    recentAlerts: limitedRecentAlerts,
    getAlertsForInstrument,
    
    // System health
    systemHealth: enableHealthMonitoring ? systemHealth : null,
    isSystemHealthy: enableHealthMonitoring ? isSystemHealthy : true,
    
    // Actions
    connect,
    disconnect,
    sendMessage
  };
};

// =============================================================================
// SPECIALIZED HOOKS
// =============================================================================

/**
 * Hook for monitoring specific instruments with real-time price updates
 */
export const useInstrumentWatch = (instruments: Instrument[]) => {
  const instrumentIds = instruments.map(i => i.id);
  
  const { realtimeData, getLatestPrice, isConnected } = useRealTimeData({
    instrumentIds,
    enableHealthMonitoring: false
  });

  const instrumentsWithPrices = useMemo(() => {
    return instruments.map(instrument => ({
      ...instrument,
      currentPrice: getLatestPrice(instrument.id),
      realtimeData: realtimeData[instrument.id] || null,
      isLive: isConnected && !!realtimeData[instrument.id],
      priceChange: calculatePriceChange(instrument, realtimeData[instrument.id]),
      status: determineInstrumentStatus(instrument, realtimeData[instrument.id], isConnected)
    }));
  }, [instruments, realtimeData, getLatestPrice, isConnected]);

  return {
    instruments: instrumentsWithPrices,
    isConnected,
    realtimeData
  };
};

/**
 * Hook for alert monitoring with real-time updates
 */
export const useAlertMonitor = () => {
  const { 
    recentAlerts, 
    isConnected, 
    getAlertsForInstrument 
  } = useRealTimeData({
    maxAlerts: 100,
    enableHealthMonitoring: false
  });

  const alertsByInstrument = useMemo(() => {
    const grouped: Record<number, AlertLogWithDetails[]> = {};
    recentAlerts.forEach(alert => {
      if (!grouped[alert.instrumentId]) {
        grouped[alert.instrumentId] = [];
      }
      grouped[alert.instrumentId].push(alert);
    });
    return grouped;
  }, [recentAlerts]);

  const alertStats = useMemo(() => {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    return {
      total: recentAlerts.length,
      lastHour: recentAlerts.filter(alert => 
        new Date(alert.timestamp) >= oneHourAgo
      ).length,
      lastDay: recentAlerts.filter(alert => 
        new Date(alert.timestamp) >= oneDayAgo
      ).length
    };
  }, [recentAlerts]);

  return {
    recentAlerts,
    alertsByInstrument,
    alertStats,
    isConnected,
    getAlertsForInstrument
  };
};

/**
 * Hook for system health monitoring
 */
export const useSystemHealthMonitor = () => {
  const { 
    systemHealth, 
    isSystemHealthy, 
    isConnected 
  } = useRealTimeData({
    enableHealthMonitoring: true
  });

  const healthMetrics = useMemo(() => {
    if (!systemHealth) return null;

    return {
      uptime: null, // Not available in Phase 4 structure
      activeConnections: systemHealth.activeInstruments,
      maxConnections: null, // Not available in Phase 4 structure
      avgEvaluationTime: null, // Not available in Phase 4 structure
      alertsLastHour: null, // Not available in Phase 4 structure
      schwabApiStatus: systemHealth.apiConnected ? 'connected' : 'disconnected',
      databaseConnections: systemHealth.historicalDataService?.serviceRunning ? 1 : 0
    };
  }, [systemHealth]);

  return {
    systemHealth,
    healthMetrics,
    isSystemHealthy,
    isConnected
  };
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function calculatePriceChange(instrument: Instrument, marketData: MarketData | null): number | null {
  if (!marketData?.price || !instrument.lastPrice) {
    return null;
  }
  
  return ((marketData.price - instrument.lastPrice) / instrument.lastPrice) * 100;
}

function determineInstrumentStatus(
  instrument: Instrument, 
  marketData: MarketData | null, 
  isConnected: boolean
): InstrumentStatus {
  if (!isConnected) {
    return InstrumentStatus.ERROR;
  }
  
  if (!marketData) {
    return instrument.status;
  }
  
  // Check if data is stale (older than 5 minutes)
  const dataAge = new Date().getTime() - new Date(marketData.timestamp).getTime();
  if (dataAge > 5 * 60 * 1000) {
    return InstrumentStatus.INACTIVE;
  }
  
  return InstrumentStatus.ACTIVE;
}