/**
 * AlertHistory Component
 * 
 * Complete alert history and analytics interface with paginated display,
 * advanced filtering, export functionality, and performance analytics.
 * Optimized for handling large datasets with efficient querying.
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, queryKeys } from '../../services/apiClient';
import {
  AlertLogWithDetails,
  AlertStats,
  AlertStatus,
  DeliveryStatus,
  RuleCondition,
  AlertLogFilters,
  PaginationParams,
  Instrument,
  AlertRule,
  InstrumentStatus
} from '../../types';

// =============================================================================
// TYPES
// =============================================================================

interface AlertHistoryProps {
  className?: string;
}

interface ExportOptions {
  format: 'csv' | 'json';
  dateRange: {
    start: string;
    end: string;
  };
  includeAll: boolean;
}

interface DateRangePreset {
  label: string;
  days: number;
}

// Date range presets
const DATE_PRESETS: DateRangePreset[] = [
  { label: 'Last 24 Hours', days: 1 },
  { label: 'Last 7 Days', days: 7 },
  { label: 'Last 30 Days', days: 30 },
  { label: 'Last 90 Days', days: 90 }
];

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

const getDateRangeFromPreset = (days: number) => {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - days);
  
  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0]
  };
};

const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date);
};

const formatDuration = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
};

const getStatusColor = (status: AlertStatus | DeliveryStatus): string => {
  switch (status) {
    case AlertStatus.FIRED:
    case DeliveryStatus.ALL_DELIVERED:
      return 'success';
    case AlertStatus.SUPPRESSED:
    case DeliveryStatus.PENDING:
      return 'warning';
    case AlertStatus.ERROR:
    case DeliveryStatus.FAILED:
      return 'error';
    default:
      return 'info';
  }
};

const exportToCsv = (alerts: AlertLogWithDetails[]): string => {
  const headers = [
    'Timestamp',
    'Instrument',
    'Rule Name',
    'Condition',
    'Trigger Value',
    'Threshold',
    'Status',
    'Delivery Status',
    'Evaluation Time (ms)',
    'Message'
  ];
  
  const rows = alerts.map(alert => [
    alert.timestamp,
    alert.instrument?.symbol || 'Unknown',
    alert.rule?.name || `Rule ${alert.rule_id}`,
    alert.rule_condition,
    alert.trigger_value,
    alert.threshold_value,
    alert.fired_status,
    alert.delivery_status,
    alert.evaluation_time_ms || 0,
    alert.alert_message || ''
  ]);
  
  return [headers, ...rows]
    .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    .join('\n');
};

const downloadFile = (content: string, filename: string, contentType: string) => {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

const AlertHistory: React.FC<AlertHistoryProps> = ({ className = '' }) => {
  const [filters, setFilters] = useState<AlertLogFilters>({});
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    per_page: 50
  });
  const [selectedAlerts, setSelectedAlerts] = useState<Set<number>>(new Set());
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'csv',
    dateRange: getDateRangeFromPreset(7),
    includeAll: false
  });
  const [isExporting, setIsExporting] = useState(false);

  // Data fetching
  const {
    data: alertsResponse,
    isLoading: alertsLoading,
    error: alertsError
  } = useQuery({
    queryKey: queryKeys.alerts(filters, pagination),
    queryFn: () => apiClient.getAlerts(filters, pagination),
    refetchInterval: 30000,
    keepPreviousData: true
  });

  const {
    data: stats,
    isLoading: statsLoading
  } = useQuery({
    queryKey: queryKeys.alertStats(),
    queryFn: () => apiClient.getAlertStats(),
    refetchInterval: 60000
  });

  const {
    data: instruments = []
  } = useQuery({
    queryKey: queryKeys.instruments({ status: InstrumentStatus.ACTIVE }),
    queryFn: () => apiClient.getInstruments({ status: InstrumentStatus.ACTIVE })
  });

  const {
    data: rules = []
  } = useQuery({
    queryKey: queryKeys.alertRules(),
    queryFn: () => apiClient.getAlertRules()
  });

  // Event handlers
  const handleFilterChange = useCallback((newFilters: Partial<AlertLogFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setPagination(prev => ({ ...prev, page: 1 })); // Reset to first page
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setPagination(prev => ({ ...prev, page }));
  }, []);

  const handlePerPageChange = useCallback((perPage: number) => {
    setPagination({ page: 1, per_page: perPage });
  }, []);

  const handleDatePreset = useCallback((days: number) => {
    const range = getDateRangeFromPreset(days);
    handleFilterChange({
      start_date: range.start,
      end_date: range.end
    });
  }, [handleFilterChange]);

  const handleSelectAlert = useCallback((alertId: number, selected: boolean) => {
    const newSelection = new Set(selectedAlerts);
    if (selected) {
      newSelection.add(alertId);
    } else {
      newSelection.delete(alertId);
    }
    setSelectedAlerts(newSelection);
  }, [selectedAlerts]);

  const handleSelectAll = useCallback((selected: boolean) => {
    if (selected && alertsResponse?.items) {
      setSelectedAlerts(new Set(alertsResponse.items.map(alert => alert.id)));
    } else {
      setSelectedAlerts(new Set());
    }
  }, [alertsResponse?.items]);

  const handleExport = useCallback(async () => {
    setIsExporting(true);
    try {
      let alertsToExport: AlertLogWithDetails[];
      
      if (exportOptions.includeAll) {
        // Export all alerts with date range filter
        const exportFilters: AlertLogFilters = {
          start_date: exportOptions.dateRange.start,
          end_date: exportOptions.dateRange.end
        };
        const allAlertsResponse = await apiClient.getAlerts(exportFilters, { page: 1, per_page: 10000 });
        alertsToExport = allAlertsResponse.items;
      } else {
        // Export only selected alerts
        alertsToExport = alertsResponse?.items.filter(alert => selectedAlerts.has(alert.id)) || [];
      }
      
      if (alertsToExport.length === 0) {
        alert('No alerts to export');
        return;
      }
      
      const timestamp = new Date().toISOString().split('T')[0];
      
      if (exportOptions.format === 'csv') {
        const csvContent = exportToCsv(alertsToExport);
        downloadFile(csvContent, `alerts_${timestamp}.csv`, 'text/csv');
      } else {
        const jsonContent = JSON.stringify(alertsToExport, null, 2);
        downloadFile(jsonContent, `alerts_${timestamp}.json`, 'application/json');
      }
      
      setShowExportModal(false);
      setSelectedAlerts(new Set());
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  }, [exportOptions, alertsResponse?.items, selectedAlerts]);

  // Computed values
  const alerts = alertsResponse?.items || [];
  const totalPages = Math.ceil((alertsResponse?.total || 0) / (pagination.per_page || 25));
  
  const filteredStats = useMemo(() => {
    if (!stats) return null;
    
    return {
      ...stats,
      // Add computed stats based on current filters if needed
      filtered_count: alertsResponse?.total || 0
    };
  }, [stats, alertsResponse?.total]);

  if (alertsLoading && !alertsResponse) {
    return (
      <div className={`alert-history ${className}`}>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading alert history...</p>
        </div>
      </div>
    );
  }

  if (alertsError) {
    return (
      <div className={`alert-history ${className}`}>
        <div className="error-container">
          <h2>Error Loading Alert History</h2>
          <p>Failed to load alert history. Please try refreshing the page.</p>
          <button onClick={() => window.location.reload()} className="btn btn-primary">
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`alert-history ${className}`}>
      {/* Header with Stats */}
      <div className="history-header">
        <div className="header-left">
          <h2>Alert History & Analytics</h2>
          <p>{alertsResponse?.total || 0} total alerts</p>
        </div>
        <div className="header-actions">
          <button 
            onClick={() => setShowExportModal(true)}
            className="btn btn-secondary"
            disabled={alerts.length === 0}
          >
            Export Data
          </button>
        </div>
      </div>

      {/* Statistics Dashboard */}
      {stats && !statsLoading && (
        <div className="stats-dashboard">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{stats.total_alerts_this_week?.toLocaleString() || '0'}</div>
              <div className="stat-label">Total Alerts (Week)</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.total_alerts_today?.toLocaleString() || '0'}</div>
              <div className="stat-label">Today</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.avg_evaluation_time_ms ? formatDuration(stats.avg_evaluation_time_ms) : 'N/A'}</div>
              <div className="stat-label">Avg Eval Time</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.fastest_evaluation_ms || 'N/A'}</div>
              <div className="stat-label">Fastest</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.slowest_evaluation_ms || 'N/A'}</div>
              <div className="stat-label">Slowest</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="history-filters">
        <div className="filter-row">
          <div className="filter-group">
            <label>Date Range:</label>
            <div className="date-presets">
              {DATE_PRESETS.map(preset => (
                <button
                  key={preset.label}
                  onClick={() => handleDatePreset(preset.days)}
                  className="preset-button"
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
        </div>
        
        <div className="filter-row">
          <div className="filter-group">
            <label>From:</label>
            <input
              type="date"
              value={filters.start_date || ''}
              onChange={(e) => handleFilterChange({ start_date: e.target.value || undefined })}
              className="date-input"
            />
          </div>
          
          <div className="filter-group">
            <label>To:</label>
            <input
              type="date"
              value={filters.end_date || ''}
              onChange={(e) => handleFilterChange({ end_date: e.target.value || undefined })}
              className="date-input"
            />
          </div>
          
          <div className="filter-group">
            <label>Status:</label>
            <select 
              value={filters.fired_status || ''} 
              onChange={(e) => handleFilterChange({
                fired_status: e.target.value as AlertStatus || undefined
              })}
              className="filter-select"
            >
              <option value="">All Statuses</option>
              {Object.values(AlertStatus).map(status => (
                <option key={status} value={status}>{status.toUpperCase()}</option>
              ))}
            </select>
          </div>
          
          <div className="filter-group">
            <label>Delivery:</label>
            <select 
              value={filters.delivery_status || ''} 
              onChange={(e) => handleFilterChange({
                delivery_status: e.target.value as DeliveryStatus || undefined
              })}
              className="filter-select"
            >
              <option value="">All Delivery</option>
              {Object.values(DeliveryStatus).map(status => (
                <option key={status} value={status}>{status.replace('_', ' ').toUpperCase()}</option>
              ))}
            </select>
          </div>
          
          <div className="filter-group">
            <label>Instrument:</label>
            <select 
              value={filters.instrument_id || ''} 
              onChange={(e) => handleFilterChange({
                instrument_id: e.target.value ? parseInt(e.target.value) : undefined
              })}
              className="filter-select"
            >
              <option value="">All Instruments</option>
              {instruments.map(instrument => (
                <option key={instrument.id} value={instrument.id}>{instrument.symbol}</option>
              ))}
            </select>
          </div>
          
          <div className="filter-group">
            <label>Rule:</label>
            <select 
              value={filters.rule_id || ''} 
              onChange={(e) => handleFilterChange({
                rule_id: e.target.value ? parseInt(e.target.value) : undefined
              })}
              className="filter-select"
            >
              <option value="">All Rules</option>
              {rules.map(rule => (
                <option key={rule.id} value={rule.id}>{rule.name || `Rule ${rule.id}`}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Selection Controls */}
      {selectedAlerts.size > 0 && (
        <div className="selection-controls">
          <span>{selectedAlerts.size} alerts selected</span>
          <button
            onClick={() => setSelectedAlerts(new Set())}
            className="btn btn-secondary btn-sm"
          >
            Clear Selection
          </button>
        </div>
      )}

      {/* Alerts Table */}
      <div className="alerts-table-container">
        {alerts.length === 0 ? (
          <div className="empty-state">
            <h3>No Alerts Found</h3>
            <p>No alerts match your current filter criteria.</p>
          </div>
        ) : (
          <>
            <div className="alerts-table">
              <div className="table-header">
                <div className="col-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedAlerts.size === alerts.length && alerts.length > 0}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                  />
                </div>
                <div className="col-timestamp">Time</div>
                <div className="col-instrument">Instrument</div>
                <div className="col-rule">Rule</div>
                <div className="col-condition">Condition</div>
                <div className="col-values">Trigger/Threshold</div>
                <div className="col-status">Alert Status</div>
                <div className="col-delivery">Delivery</div>
                <div className="col-eval-time">Eval Time</div>
              </div>
              
              {alerts.map(alert => (
                <div key={alert.id} className="table-row">
                  <div className="col-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedAlerts.has(alert.id)}
                      onChange={(e) => handleSelectAlert(alert.id, e.target.checked)}
                    />
                  </div>
                  <div className="col-timestamp">
                    <span className="timestamp">{formatDateTime(alert.timestamp)}</span>
                  </div>
                  <div className="col-instrument">
                    <span className="instrument-symbol">
                      {alert.instrument?.symbol || 'Unknown'}
                    </span>
                  </div>
                  <div className="col-rule">
                    <div className="rule-name">{alert.rule?.name || `Rule ${alert.rule_id}`}</div>
                    {alert.alert_message && (
                      <div className="alert-message">{alert.alert_message}</div>
                    )}
                  </div>
                  <div className="col-condition">
                    <span className="condition">{alert.rule_condition.replace('_', ' ')}</span>
                  </div>
                  <div className="col-values">
                    <div className="values">
                      <span className="trigger-value">{alert.trigger_value.toFixed(4)}</span>
                      <span className="separator">/</span>
                      <span className="threshold-value">{alert.threshold_value.toFixed(4)}</span>
                    </div>
                  </div>
                  <div className="col-status">
                    <span className={`status-badge status-${getStatusColor(alert.fired_status)}`}>
                      {alert.fired_status}
                    </span>
                  </div>
                  <div className="col-delivery">
                    <span className={`status-badge status-${getStatusColor(alert.delivery_status)}`}>
                      {alert.delivery_status.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="col-eval-time">
                    <span className="eval-time">
                      {alert.evaluation_time_ms ? formatDuration(alert.evaluation_time_ms) : 'N/A'}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            <div className="pagination-container">
              <div className="pagination-info">
                <span>
                  Showing {(((pagination.page || 1) - 1) * (pagination.per_page || 25)) + 1} to{' '}
                  {Math.min((pagination.page || 1) * (pagination.per_page || 25), alertsResponse?.total || 0)} of{' '}
                  {alertsResponse?.total || 0} alerts
                </span>
                <select
                  value={pagination.per_page || 25}
                  onChange={(e) => handlePerPageChange(parseInt(e.target.value))}
                  className="per-page-select"
                >
                  <option value={25}>25 per page</option>
                  <option value={50}>50 per page</option>
                  <option value={100}>100 per page</option>
                  <option value={200}>200 per page</option>
                </select>
              </div>
              
              <div className="pagination-controls">
                <button
                  onClick={() => handlePageChange(1)}
                  disabled={(pagination.page || 1) === 1}
                  className="btn btn-secondary btn-sm"
                >
                  First
                </button>
                <button
                  onClick={() => handlePageChange((pagination.page || 1) - 1)}
                  disabled={(pagination.page || 1) === 1}
                  className="btn btn-secondary btn-sm"
                >
                  Previous
                </button>
                
                <span className="page-info">
                  Page {pagination.page || 1} of {totalPages}
                </span>
                
                <button
                  onClick={() => handlePageChange((pagination.page || 1) + 1)}
                  disabled={(pagination.page || 1) === totalPages}
                  className="btn btn-secondary btn-sm"
                >
                  Next
                </button>
                <button
                  onClick={() => handlePageChange(totalPages)}
                  disabled={(pagination.page || 1) === totalPages}
                  className="btn btn-secondary btn-sm"
                >
                  Last
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <div className="modal-overlay" onClick={() => setShowExportModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Export Alert Data</h3>
              <button 
                onClick={() => setShowExportModal(false)} 
                className="close-button"
              >
                ×
              </button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label>Export Format:</label>
                <div className="radio-group">
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="format"
                      value="csv"
                      checked={exportOptions.format === 'csv'}
                      onChange={(e) => setExportOptions({
                        ...exportOptions,
                        format: e.target.value as 'csv' | 'json'
                      })}
                    />
                    CSV (Excel compatible)
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="format"
                      value="json"
                      checked={exportOptions.format === 'json'}
                      onChange={(e) => setExportOptions({
                        ...exportOptions,
                        format: e.target.value as 'csv' | 'json'
                      })}
                    />
                    JSON (for analysis tools)
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={exportOptions.includeAll}
                    onChange={(e) => setExportOptions({
                      ...exportOptions,
                      includeAll: e.target.checked
                    })}
                  />
                  Export all alerts (ignore current selection)
                </label>
              </div>

              {exportOptions.includeAll && (
                <div className="form-row">
                  <div className="form-group">
                    <label>Start Date:</label>
                    <input
                      type="date"
                      value={exportOptions.dateRange.start}
                      onChange={(e) => setExportOptions({
                        ...exportOptions,
                        dateRange: {
                          ...exportOptions.dateRange,
                          start: e.target.value
                        }
                      })}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label>End Date:</label>
                    <input
                      type="date"
                      value={exportOptions.dateRange.end}
                      onChange={(e) => setExportOptions({
                        ...exportOptions,
                        dateRange: {
                          ...exportOptions.dateRange,
                          end: e.target.value
                        }
                      })}
                      className="form-input"
                    />
                  </div>
                </div>
              )}

              {!exportOptions.includeAll && (
                <div className="export-summary">
                  <p>Will export {selectedAlerts.size} selected alerts</p>
                  {selectedAlerts.size === 0 && (
                    <p className="warning">Please select some alerts first or choose "Export all alerts"</p>
                  )}
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button 
                onClick={() => setShowExportModal(false)}
                className="btn btn-secondary"
                disabled={isExporting}
              >
                Cancel
              </button>
              <button 
                onClick={handleExport}
                className="btn btn-primary"
                disabled={isExporting || (!exportOptions.includeAll && selectedAlerts.size === 0)}
              >
                {isExporting ? 'Exporting...' : 'Export Data'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertHistory;