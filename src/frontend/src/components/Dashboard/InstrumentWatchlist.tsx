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
    data: instruments = [],
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: queryKeys.instruments({ status: InstrumentStatus.ACTIVE }),
    queryFn: () => apiClient.getInstruments({ status: InstrumentStatus.ACTIVE }),
    refetchInterval: 30000, // Refetch every 30 seconds as fallback
    staleTime: 10000 // Consider data fresh for 10 seconds
  });

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
        {formatPrice(currentPrice ?? instrument.last_price ?? null)}
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

// =============================================================================
// STYLES (to be moved to CSS file)
// =============================================================================

// Note: These styles should be moved to a separate CSS file in production
const watchlistStyles = `
.watchlist-container {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.watchlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
}

.watchlist-title h3 {
  margin: 0;
  color: #ffffff;
  font-size: 18px;
  font-weight: 600;
}

.instrument-count {
  color: #888;
  font-size: 14px;
  margin-left: 8px;
}

.watchlist-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
}

.connection-status.connected {
  color: #00d4aa;
}

.connection-status.disconnected {
  color: #ff5555;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.refresh-button {
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #ffffff;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.refresh-button:hover {
  background: rgba(255, 255, 255, 0.05);
}

.watchlist-table {
  display: flex;
  flex-direction: column;
}

.watchlist-header-row {
  display: grid;
  grid-template-columns: 100px 200px 80px 100px 80px 80px 100px;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 12px;
  font-weight: 600;
  color: #aaa;
  text-transform: uppercase;
}

.watchlist-row {
  display: grid;
  grid-template-columns: 100px 200px 80px 100px 80px 80px 100px;
  gap: 12px;
  padding: 12px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background-color 0.15s ease;
}

.watchlist-row:hover {
  background: rgba(255, 255, 255, 0.02);
}

.cell {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.cell.symbol {
  font-weight: 600;
  position: relative;
}

.live-indicator {
  position: absolute;
  top: -2px;
  right: -8px;
  width: 6px;
  height: 6px;
  background: #00d4aa;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.cell.name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.type-badge {
  padding: 2px 6px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}

.type-badge.future {
  background: rgba(0, 123, 255, 0.2);
  color: #007bff;
}

.type-badge.index {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

.type-badge.internal {
  background: rgba(108, 117, 125, 0.2);
  color: #6c757d;
}

.cell.positive {
  color: #00d4aa;
}

.cell.negative {
  color: #ff5555;
}

.cell.neutral {
  color: #888;
}

.add-alert-button {
  background: rgba(0, 212, 170, 0.1);
  border: 1px solid rgba(0, 212, 170, 0.3);
  color: #00d4aa;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.add-alert-button:hover {
  background: rgba(0, 212, 170, 0.2);
  border-color: rgba(0, 212, 170, 0.5);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.watchlist-loading,
.watchlist-error,
.watchlist-empty {
  padding: 40px 20px;
  text-align: center;
  color: #888;
}

.skeleton-row {
  height: 48px;
  background: rgba(255, 255, 255, 0.05);
  margin: 8px 0;
  border-radius: 4px;
  animation: skeleton-loading 1.5s ease-in-out infinite alternate;
}

@keyframes skeleton-loading {
  0% { opacity: 0.3; }
  100% { opacity: 0.7; }
}

.retry-button {
  background: rgba(255, 85, 85, 0.1);
  border: 1px solid rgba(255, 85, 85, 0.3);
  color: #ff5555;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 16px;
}
`;

export default InstrumentWatchlist;