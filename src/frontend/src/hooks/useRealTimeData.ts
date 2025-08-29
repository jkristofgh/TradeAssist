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
  sendMessage: (message: object) => void;
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
    return recentAlerts.filter(alert => alert.instrument_id === instrumentId);
  }, [recentAlerts]);

  const isSystemHealthy = useMemo(() => {
    if (!systemHealth) return false;
    
    return systemHealth.status === 'healthy' &&
           systemHealth.database.status === 'connected' &&
           systemHealth.alert_engine.status === 'running';
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
      if (!grouped[alert.instrument_id]) {
        grouped[alert.instrument_id] = [];
      }
      grouped[alert.instrument_id].push(alert);
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
      uptime: Math.floor(systemHealth.uptime_seconds / 60), // minutes
      activeConnections: systemHealth.websocket.active_connections,
      maxConnections: systemHealth.websocket.max_connections,
      avgEvaluationTime: systemHealth.alert_engine.avg_evaluation_time_ms,
      alertsLastHour: systemHealth.alert_engine.alerts_fired_last_hour,
      schwabApiStatus: systemHealth.schwab_api.status,
      databaseConnections: systemHealth.database.active_connections
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
  if (!marketData?.price || !instrument.last_price) {
    return null;
  }
  
  return ((marketData.price - instrument.last_price) / instrument.last_price) * 100;
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