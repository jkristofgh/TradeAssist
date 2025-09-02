/**
 * InstrumentWatchlist Component
 * 
 * Real-time instrument monitoring with live price updates, color-coded status indicators,
 * and quick alert rule creation functionality. Optimized for <50ms WebSocket update rendering.
 */

import React, { useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, queryKeys } from '../../services/apiClient';
import { useInstrumentWatch } from '../../hooks/useRealTimeData';
import { Instrument, InstrumentStatus, InstrumentType } from '../../types';
import './InstrumentWatchlist.css';

// =============================================================================
// TYPES
// =============================================================================

interface InstrumentWatchlistProps {
  onAddAlert?: (instrumentId: number) => void;
  maxInstruments?: number;
  showAddButton?: boolean;
  className?: string;
}

interface InstrumentRowProps {
  instrument: Instrument;
  currentPrice: number | null;
  priceChange: number | null;
  isLive: boolean;
  onAddAlert?: (instrumentId: number) => void;
  showAddButton?: boolean;
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export const InstrumentWatchlist: React.FC<InstrumentWatchlistProps> = ({
  onAddAlert,
  maxInstruments = 15,
  showAddButton = true,
  className = ''
}) => {
  // Fetch instruments from API
  const {
    data: instrumentsData,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: queryKeys.instruments({ status: InstrumentStatus.ACTIVE }),
    queryFn: () => apiClient.getInstruments({ status: InstrumentStatus.ACTIVE }),
    refetchInterval: 30000, // Refetch every 30 seconds as fallback
    staleTime: 10000 // Consider data fresh for 10 seconds
  });

  // Ensure instruments is always an array
  const instruments = useMemo(() => 
    Array.isArray(instrumentsData) ? instrumentsData : [], 
    [instrumentsData]
  );

  // Limit instruments for performance
  const limitedInstruments = useMemo(() => 
    instruments.slice(0, maxInstruments), 
    [instruments, maxInstruments]
  );

  // Get real-time data for instruments
  const { instruments: instrumentsWithData, isConnected } = useInstrumentWatch(limitedInstruments);

  // Sort instruments by symbol for consistent display
  const sortedInstruments = useMemo(() =>
    [...instrumentsWithData].sort((a, b) => a.symbol.localeCompare(b.symbol)),
    [instrumentsWithData]
  );

  // =============================================================================
  // EVENT HANDLERS
  // =============================================================================

  const handleAddAlert = useCallback((instrumentId: number) => {
    onAddAlert?.(instrumentId);
  }, [onAddAlert]);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  // =============================================================================
  // RENDER
  // =============================================================================

  if (isLoading) {
    return (
      <div className={`watchlist-container ${className}`}>
        <WatchlistHeader 
          isConnected={isConnected}
          onRefresh={handleRefresh}
          isLoading={true}
        />
        <div className="watchlist-loading">
          <div className="loading-skeleton">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="skeleton-row" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`watchlist-container ${className}`}>
        <WatchlistHeader 
          isConnected={isConnected}
          onRefresh={handleRefresh}
          isLoading={false}
        />
        <div className="watchlist-error">
          <p>Failed to load instruments</p>
          <button onClick={handleRefresh} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`watchlist-container ${className}`}>
      <WatchlistHeader 
        isConnected={isConnected}
        onRefresh={handleRefresh}
        isLoading={false}
        count={sortedInstruments.length}
      />
      
      <div className="watchlist-table">
        <WatchlistTableHeader />
        <div className="watchlist-body">
          {sortedInstruments.map((instrument) => (
            <InstrumentRow
              key={instrument.id}
              instrument={instrument}
              currentPrice={instrument.currentPrice}
              priceChange={instrument.priceChange}
              isLive={instrument.isLive}
              onAddAlert={handleAddAlert}
              showAddButton={showAddButton}
            />
          ))}
        </div>
      </div>
      
      {sortedInstruments.length === 0 && (
        <div className="watchlist-empty">
          <p>No active instruments to monitor</p>
        </div>
      )}
    </div>
  );
};

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

interface WatchlistHeaderProps {
  isConnected: boolean;
  onRefresh: () => void;
  isLoading: boolean;
  count?: number;
}

const WatchlistHeader: React.FC<WatchlistHeaderProps> = ({
  isConnected,
  onRefresh,
  isLoading,
  count
}) => (
  <div className="watchlist-header">
    <div className="watchlist-title">
      <h3>Market Watch</h3>
      {count !== undefined && (
        <span className="instrument-count">({count} instruments)</span>
      )}
    </div>
    
    <div className="watchlist-controls">
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        <div className="status-indicator" />
        <span>{isConnected ? 'Live' : 'Offline'}</span>
      </div>
      
      <button 
        onClick={onRefresh}
        disabled={isLoading}
        className="refresh-button"
        aria-label="Refresh instruments"
      >
        🔄
      </button>
    </div>
  </div>
);

const WatchlistTableHeader: React.FC = () => (
  <div className="watchlist-header-row">
    <div className="header-cell symbol">Symbol</div>
    <div className="header-cell name">Name</div>
    <div className="header-cell type">Type</div>
    <div className="header-cell price">Price</div>
    <div className="header-cell change">Change</div>
    <div className="header-cell status">Status</div>
    <div className="header-cell actions">Actions</div>
  </div>
);

const InstrumentRow: React.FC<InstrumentRowProps> = ({
  instrument,
  currentPrice,
  priceChange,
  isLive,
  onAddAlert,
  showAddButton
}) => {
  const priceChangeClass = useMemo(() => {
    if (!priceChange) return 'neutral';
    return priceChange > 0 ? 'positive' : 'negative';
  }, [priceChange]);

  const statusClass = useMemo(() => {
    if (!isLive) return 'offline';
    switch (instrument.status) {
      case InstrumentStatus.ACTIVE: return 'active';
      case InstrumentStatus.INACTIVE: return 'inactive';
      case InstrumentStatus.ERROR: return 'error';
      default: return 'unknown';
    }
  }, [instrument.status, isLive]);

  const formatPrice = useCallback((price: number | null): string => {
    if (price === null) return '-';
    return price.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 4
    });
  }, []);

  const formatPriceChange = useCallback((change: number | null): string => {
    if (change === null) return '-';
    const sign = change > 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  }, []);

  const getTypeDisplay = useCallback((type: InstrumentType): string => {
    switch (type) {
      case InstrumentType.FUTURE: return 'Future';
      case InstrumentType.INDEX: return 'Index';
      case InstrumentType.INTERNAL: return 'Internal';
      default: return type;
    }
  }, []);

  return (
    <div className={`watchlist-row ${statusClass}`}>
      <div className="cell symbol">
        <strong>{instrument.symbol}</strong>
        {isLive && <div className="live-indicator" />}
      </div>
      
      <div className="cell name" title={instrument.name}>
        {instrument.name}
      </div>
      
      <div className="cell type">
        <span className={`type-badge ${instrument.type}`}>
          {getTypeDisplay(instrument.type)}
        </span>
      </div>
      
      <div className={`cell price ${priceChangeClass}`}>
        {formatPrice(currentPrice ?? instrument.lastPrice ?? null)}
      </div>
      
      <div className={`cell change ${priceChangeClass}`}>
        {formatPriceChange(priceChange)}
      </div>
      
      <div className={`cell status ${statusClass}`}>
        <div className="status-indicator" />
        <span>{instrument.status}</span>
      </div>
      
      <div className="cell actions">
        {showAddButton && (
          <button
            onClick={() => onAddAlert?.(instrument.id)}
            className="add-alert-button"
            title={`Create alert for ${instrument.symbol}`}
            aria-label={`Create alert for ${instrument.symbol}`}
          >
            + Alert
          </button>
        )}
      </div>
    </div>
  );
};

export default InstrumentWatchlist;