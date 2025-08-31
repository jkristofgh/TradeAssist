/**
 * Data Preview Component
 * 
 * Component for displaying historical data results with table and chart views.
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  DataPreviewProps,
  MarketDataBar,
  TableColumn,
  TableSortConfig,
  TablePaginationConfig,
  CandlestickData
} from '../../types/historicalData';
import './DataPreview.css';

const DataPreview: React.FC<DataPreviewProps> = ({
  data,
  query,
  isLoading = false,
  onSaveQuery,
  onExport,
  onRerun
}) => {
  // =============================================================================
  // STATE
  // =============================================================================
  
  const [viewMode, setViewMode] = useState<'table' | 'chart'>('table');
  const [sortConfig, setSortConfig] = useState<TableSortConfig>({
    key: 'timestamp',
    direction: 'desc'
  });
  const [pagination, setPagination] = useState<TablePaginationConfig>({
    page: 1,
    pageSize: 50,
    totalPages: Math.ceil(data.length / 50),
    totalRecords: data.length
  });
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [queryName, setQueryName] = useState('');
  const [queryDescription, setQueryDescription] = useState('');

  // =============================================================================
  // TABLE COLUMNS
  // =============================================================================
  
  const columns: TableColumn[] = [
    {
      key: 'symbol',
      label: 'Symbol',
      sortable: true
    },
    {
      key: 'timestamp',
      label: 'Timestamp',
      sortable: true,
      format: (value: string) => new Date(value).toLocaleString()
    },
    {
      key: 'open',
      label: 'Open',
      sortable: true,
      format: (value: number) => value.toFixed(2),
      align: 'right'
    },
    {
      key: 'high',
      label: 'High',
      sortable: true,
      format: (value: number) => value.toFixed(2),
      align: 'right'
    },
    {
      key: 'low',
      label: 'Low',
      sortable: true,
      format: (value: number) => value.toFixed(2),
      align: 'right'
    },
    {
      key: 'close',
      label: 'Close',
      sortable: true,
      format: (value: number) => value.toFixed(2),
      align: 'right'
    },
    {
      key: 'volume',
      label: 'Volume',
      sortable: true,
      format: (value: number) => value.toLocaleString(),
      align: 'right'
    }
  ];

  if (data.some(d => d.vwap !== undefined)) {
    columns.push({
      key: 'vwap',
      label: 'VWAP',
      sortable: true,
      format: (value?: number) => value ? value.toFixed(2) : '-',
      align: 'right'
    });
  }

  if (data.some(d => d.openInterest !== undefined)) {
    columns.push({
      key: 'openInterest',
      label: 'Open Interest',
      sortable: true,
      format: (value?: number) => value ? value.toLocaleString() : '-',
      align: 'right'
    });
  }

  // =============================================================================
  // SORTING & PAGINATION
  // =============================================================================
  
  const sortedData = useMemo(() => {
    const sorted = [...data].sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];
      
      if (aValue === undefined || aValue === null) return 1;
      if (bValue === undefined || bValue === null) return -1;
      
      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
    
    return sorted;
  }, [data, sortConfig]);

  const paginatedData = useMemo(() => {
    const startIndex = (pagination.page - 1) * pagination.pageSize;
    const endIndex = startIndex + pagination.pageSize;
    return sortedData.slice(startIndex, endIndex);
  }, [sortedData, pagination]);

  // =============================================================================
  // CHART DATA
  // =============================================================================
  
  const chartData = useMemo(() => {
    // Group data by symbol for multi-symbol charts
    const symbolGroups = data.reduce((groups, bar) => {
      if (!groups[bar.symbol]) {
        groups[bar.symbol] = [];
      }
      groups[bar.symbol].push(bar);
      return groups;
    }, {} as Record<string, MarketDataBar[]>);

    return Object.entries(symbolGroups).map(([symbol, bars]) => ({
      symbol,
      data: bars.map(bar => ({
        x: bar.timestamp,
        o: bar.open,
        h: bar.high,
        l: bar.low,
        c: bar.close
      } as CandlestickData))
    }));
  }, [data]);

  // =============================================================================
  // HANDLERS
  // =============================================================================
  
  const handleSort = useCallback((key: keyof MarketDataBar) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  }, []);

  const handlePageChange = useCallback((newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }));
  }, []);

  const handlePageSizeChange = useCallback((newSize: number) => {
    setPagination(prev => ({
      ...prev,
      pageSize: newSize,
      page: 1,
      totalPages: Math.ceil(data.length / newSize)
    }));
  }, [data.length]);

  const handleSaveQuery = useCallback(() => {
    if (queryName.trim() && onSaveQuery) {
      onSaveQuery(queryName.trim(), queryDescription.trim() || undefined);
      setShowSaveDialog(false);
      setQueryName('');
      setQueryDescription('');
    }
  }, [queryName, queryDescription, onSaveQuery]);

  const formatNumber = (value: number | undefined, decimals: number = 2): string => {
    if (value === undefined || value === null) return '-';
    return value.toFixed(decimals);
  };

  // =============================================================================
  // RENDER
  // =============================================================================
  
  if (isLoading) {
    return (
      <div className="data-preview loading">
        <div className="spinner" />
        <p>Loading data...</p>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="data-preview empty">
        <p>No data available</p>
      </div>
    );
  }

  return (
    <div className="data-preview">
      <div className="preview-header">
        <div className="preview-info">
          <h3>Query Results</h3>
          <span className="record-count">{data.length} records</span>
        </div>
        
        <div className="preview-actions">
          <div className="view-toggle">
            <button
              className={`toggle-btn ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setViewMode('table')}
            >
              Table
            </button>
            <button
              className={`toggle-btn ${viewMode === 'chart' ? 'active' : ''}`}
              onClick={() => setViewMode('chart')}
            >
              Chart
            </button>
          </div>
          
          {onRerun && (
            <button className="btn btn-secondary" onClick={onRerun}>
              Rerun Query
            </button>
          )}
          
          {onSaveQuery && (
            <button 
              className="btn btn-secondary" 
              onClick={() => setShowSaveDialog(true)}
            >
              Save Query
            </button>
          )}
          
          {onExport && (
            <div className="export-buttons">
              <button 
                className="btn btn-secondary" 
                onClick={() => onExport('csv')}
              >
                Export CSV
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={() => onExport('json')}
              >
                Export JSON
              </button>
            </div>
          )}
        </div>
      </div>

      {viewMode === 'table' ? (
        <div className="table-view">
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  {columns.map(col => (
                    <th
                      key={col.key}
                      className={`${col.align || 'left'} ${col.sortable ? 'sortable' : ''}`}
                      onClick={() => col.sortable && handleSort(col.key)}
                    >
                      <span className="th-content">
                        {col.label}
                        {col.sortable && sortConfig.key === col.key && (
                          <span className="sort-indicator">
                            {sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}
                          </span>
                        )}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paginatedData.map((row, index) => (
                  <tr key={`${row.symbol}-${row.timestamp}-${index}`}>
                    {columns.map(col => (
                      <td key={col.key} className={col.align || 'left'}>
                        {col.format 
                          ? col.format(row[col.key] as any)
                          : row[col.key]?.toString() || '-'
                        }
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="pagination">
            <div className="page-size">
              <label>Rows per page:</label>
              <select
                value={pagination.pageSize}
                onChange={(e) => handlePageSizeChange(parseInt(e.target.value))}
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
            
            <div className="page-controls">
              <button
                onClick={() => handlePageChange(1)}
                disabled={pagination.page === 1}
              >
                First
              </button>
              <button
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={pagination.page === 1}
              >
                Previous
              </button>
              <span className="page-info">
                Page {pagination.page} of {pagination.totalPages}
              </span>
              <button
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={pagination.page === pagination.totalPages}
              >
                Next
              </button>
              <button
                onClick={() => handlePageChange(pagination.totalPages)}
                disabled={pagination.page === pagination.totalPages}
              >
                Last
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="chart-view">
          <div className="chart-placeholder">
            <p>Chart visualization coming soon!</p>
            <p className="chart-info">
              {chartData.length} symbol(s) with {data.length} total data points
            </p>
          </div>
        </div>
      )}

      {showSaveDialog && (
        <div className="modal-overlay" onClick={() => setShowSaveDialog(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Save Query</h3>
            <div className="form-group">
              <label htmlFor="queryName">Query Name *</label>
              <input
                id="queryName"
                type="text"
                value={queryName}
                onChange={(e) => setQueryName(e.target.value)}
                placeholder="Enter a name for this query"
              />
            </div>
            <div className="form-group">
              <label htmlFor="queryDescription">Description</label>
              <textarea
                id="queryDescription"
                value={queryDescription}
                onChange={(e) => setQueryDescription(e.target.value)}
                placeholder="Optional description"
                rows={3}
              />
            </div>
            <div className="modal-actions">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowSaveDialog(false)}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleSaveQuery}
                disabled={!queryName.trim()}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataPreview;