/**
 * SystemHealth Component
 * 
 * Complete system health monitoring dashboard with real-time metrics,
 * performance graphs, connection status visualization, and error rate monitoring.
 * Optimized for production monitoring and operational visibility.
 */

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, queryKeys } from '../../services/apiClient';
import { HealthStatus } from '../../types';

// =============================================================================
// TYPES
// =============================================================================

interface SystemHealthProps {
  className?: string;
}

interface HealthMetric {
  label: string;
  value: string | number;
  status: 'healthy' | 'warning' | 'error';
  trend?: 'up' | 'down' | 'stable';
  description?: string;
}

interface ServiceStatus {
  name: string;
  status: 'connected' | 'disconnected' | 'error' | 'running' | 'stopped';
  details: Record<string, any>;
  lastUpdate: string;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
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

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'healthy':
    case 'connected':
    case 'running':
      return '#00d4aa';
    case 'degraded':
    case 'warning':
      return '#ffb347';
    case 'unhealthy':
    case 'disconnected':
    case 'error':
    case 'stopped':
      return '#ff5555';
    default:
      return '#666';
  }
};

const getHealthScore = (health: HealthStatus): number => {
  let score = 100;
  
  // Overall system status impact
  if (health.status === 'degraded') score -= 20;
  if (health.status === 'unhealthy') score -= 50;
  
  // Database impact
  if (health.database.status === 'disconnected') score -= 30;
  
  // Alert engine impact
  if (health.alert_engine.status === 'stopped') score -= 25;
  if (health.alert_engine.status === 'error') score -= 35;
  if (health.alert_engine.avg_evaluation_time_ms > 100) score -= 10;
  
  // Schwab API impact
  if (health.schwab_api.status === 'disconnected') score -= 15;
  if (health.schwab_api.status === 'error') score -= 20;
  if (health.schwab_api.error_count_24h > 50) score -= 10;
  
  return Math.max(0, Math.min(100, score));
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

const SystemHealth: React.FC<SystemHealthProps> = ({ className = '' }) => {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 seconds
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  
  // Data fetching with auto-refresh
  const {
    data: health,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: queryKeys.health(),
    queryFn: () => apiClient.getDetailedHealth(),
    refetchInterval: autoRefresh ? refreshInterval : false,
    refetchIntervalInBackground: true,
    staleTime: 1000 // Consider data stale after 1 second
  });

  // Force refresh handler
  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  // Auto-refresh toggle
  const handleAutoRefreshToggle = useCallback(() => {
    setAutoRefresh(!autoRefresh);
  }, [autoRefresh]);

  // Computed values
  const healthScore = useMemo(() => {
    return health ? getHealthScore(health) : 0;
  }, [health]);

  const overallStatus = useMemo(() => {
    if (!health) return 'unknown';
    if (healthScore >= 90) return 'healthy';
    if (healthScore >= 70) return 'warning';
    return 'critical';
  }, [health, healthScore]);

  const services: ServiceStatus[] = useMemo(() => {
    if (!health) return [];
    
    return [
      {
        name: 'Database',
        status: health.database.status,
        details: {
          'Connection Pool': health.database.connection_pool_size,
          'Active Connections': health.database.active_connections,
          'Pool Usage': `${Math.round((health.database.active_connections / health.database.connection_pool_size) * 100)}%`
        },
        lastUpdate: health.timestamp
      },
      {
        name: 'WebSocket Server',
        status: health.websocket.active_connections > 0 ? 'running' : 'stopped',
        details: {
          'Active Connections': health.websocket.active_connections,
          'Max Connections': health.websocket.max_connections,
          'Capacity Usage': `${Math.round((health.websocket.active_connections / health.websocket.max_connections) * 100)}%`
        },
        lastUpdate: health.timestamp
      },
      {
        name: 'Alert Engine',
        status: health.alert_engine.status,
        details: {
          'Active Rules': health.alert_engine.rules_active,
          'Total Rules': health.alert_engine.rules_total,
          'Avg Eval Time': `${health.alert_engine.avg_evaluation_time_ms.toFixed(1)}ms`,
          'Alerts Last Hour': health.alert_engine.alerts_fired_last_hour
        },
        lastUpdate: health.timestamp
      },
      {
        name: 'Schwab API',
        status: health.schwab_api.status,
        details: {
          'Requests (24h)': health.schwab_api.request_count_24h.toLocaleString(),
          'Errors (24h)': health.schwab_api.error_count_24h.toLocaleString(),
          'Error Rate': `${((health.schwab_api.error_count_24h / Math.max(health.schwab_api.request_count_24h, 1)) * 100).toFixed(2)}%`,
          'Last Success': health.schwab_api.last_successful_request ? formatDateTime(health.schwab_api.last_successful_request) : 'Never'
        },
        lastUpdate: health.timestamp
      }
    ];
  }, [health]);

  const keyMetrics: HealthMetric[] = useMemo(() => {
    if (!health) return [];
    
    return [
      {
        label: 'System Uptime',
        value: formatUptime(health.uptime_seconds),
        status: health.uptime_seconds > 86400 ? 'healthy' : 'warning',
        description: 'Time since system started'
      },
      {
        label: 'Health Score',
        value: `${healthScore}%`,
        status: healthScore >= 90 ? 'healthy' : healthScore >= 70 ? 'warning' : 'error',
        description: 'Overall system health composite score'
      },
      {
        label: 'Alert Response Time',
        value: `${health.alert_engine.avg_evaluation_time_ms.toFixed(1)}ms`,
        status: health.alert_engine.avg_evaluation_time_ms < 50 ? 'healthy' : health.alert_engine.avg_evaluation_time_ms < 100 ? 'warning' : 'error',
        description: 'Average time to evaluate alert rules'
      },
      {
        label: 'Database Performance',
        value: `${Math.round((health.database.active_connections / health.database.connection_pool_size) * 100)}%`,
        status: health.database.active_connections / health.database.connection_pool_size < 0.8 ? 'healthy' : 'warning',
        description: 'Database connection pool usage'
      },
      {
        label: 'API Success Rate',
        value: `${(100 - (health.schwab_api.error_count_24h / Math.max(health.schwab_api.request_count_24h, 1)) * 100).toFixed(1)}%`,
        status: health.schwab_api.error_count_24h / Math.max(health.schwab_api.request_count_24h, 1) < 0.05 ? 'healthy' : health.schwab_api.error_count_24h / Math.max(health.schwab_api.request_count_24h, 1) < 0.1 ? 'warning' : 'error',
        description: 'Schwab API request success rate (24h)'
      },
      {
        label: 'Active Alerts',
        value: health.alert_engine.alerts_fired_last_hour,
        status: health.alert_engine.alerts_fired_last_hour < 100 ? 'healthy' : health.alert_engine.alerts_fired_last_hour < 500 ? 'warning' : 'error',
        description: 'Alerts fired in the last hour'
      }
    ];
  }, [health, healthScore]);

  if (isLoading && !health) {
    return (
      <div className={`system-health ${className}`}>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading system health...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`system-health ${className}`}>
        <div className="error-container">
          <h2>Health Monitor Unavailable</h2>
          <p>Unable to retrieve system health status. This may indicate a critical system issue.</p>
          <button onClick={handleRefresh} className="btn btn-danger">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`system-health ${className}`}>
      {/* Header */}
      <div className="health-header">
        <div className="header-left">
          <h2>System Health Monitoring</h2>
          <div className="health-status-indicator">
            <div 
              className={`status-dot status-${overallStatus}`}
              style={{ backgroundColor: getStatusColor(overallStatus) }}
            ></div>
            <span className="status-text">
              System is {overallStatus === 'healthy' ? 'Healthy' : overallStatus === 'warning' ? 'Degraded' : 'Critical'}
            </span>
            <span className="last-updated">
              Last updated: {health ? formatDateTime(health.timestamp) : 'Unknown'}
            </span>
          </div>
        </div>
        <div className="header-actions">
          <div className="refresh-controls">
            <label className="refresh-toggle">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={handleAutoRefreshToggle}
              />
              Auto-refresh
            </label>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
              disabled={!autoRefresh}
              className="refresh-interval"
            >
              <option value={1000}>1s</option>
              <option value={5000}>5s</option>
              <option value={10000}>10s</option>
              <option value={30000}>30s</option>
            </select>
          </div>
          <button onClick={handleRefresh} className="btn btn-secondary">
            Refresh Now
          </button>
        </div>
      </div>

      {/* Key Metrics Overview */}
      <div className="metrics-overview">
        <h3>Key Performance Indicators</h3>
        <div className="metrics-grid">
          {keyMetrics.map((metric, index) => (
            <div key={index} className="metric-card">
              <div className="metric-header">
                <span className="metric-label">{metric.label}</span>
                <div 
                  className={`metric-status status-${metric.status}`}
                  style={{ backgroundColor: getStatusColor(metric.status) }}
                ></div>
              </div>
              <div className="metric-value">{metric.value}</div>
              {metric.description && (
                <div className="metric-description">{metric.description}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Service Status Grid */}
      <div className="services-grid">
        <h3>Service Status</h3>
        <div className="services-container">
          {services.map((service, index) => (
            <div key={index} className="service-card">
              <div className="service-header">
                <div className="service-name">{service.name}</div>
                <div className="service-status">
                  <div 
                    className={`status-indicator status-${service.status}`}
                    style={{ backgroundColor: getStatusColor(service.status) }}
                  ></div>
                  <span className="status-label">
                    {service.status.charAt(0).toUpperCase() + service.status.slice(1)}
                  </span>
                </div>
              </div>
              <div className="service-details">
                {Object.entries(service.details).map(([key, value]) => (
                  <div key={key} className="detail-row">
                    <span className="detail-label">{key}:</span>
                    <span className="detail-value">{value}</span>
                  </div>
                ))}
              </div>
              <div className="service-footer">
                <span className="last-update">Updated: {formatDateTime(service.lastUpdate)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Information */}
      {health && (
        <div className="system-info">
          <h3>System Information</h3>
          <div className="info-grid">
            <div className="info-section">
              <h4>Application</h4>
              <div className="info-item">
                <span className="info-label">Version:</span>
                <span className="info-value">{health.version}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Uptime:</span>
                <span className="info-value">{formatUptime(health.uptime_seconds)}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Status:</span>
                <span className={`info-value status-text status-${health.status}`}>
                  {health.status.charAt(0).toUpperCase() + health.status.slice(1)}
                </span>
              </div>
            </div>
            
            <div className="info-section">
              <h4>Performance</h4>
              <div className="info-item">
                <span className="info-label">Alert Rules:</span>
                <span className="info-value">
                  {health.alert_engine.rules_active} / {health.alert_engine.rules_total} active
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Eval Time:</span>
                <span className="info-value">{health.alert_engine.avg_evaluation_time_ms.toFixed(2)}ms avg</span>
              </div>
              <div className="info-item">
                <span className="info-label">Alerts/Hour:</span>
                <span className="info-value">{health.alert_engine.alerts_fired_last_hour}</span>
              </div>
            </div>
            
            <div className="info-section">
              <h4>Resources</h4>
              <div className="info-item">
                <span className="info-label">DB Connections:</span>
                <span className="info-value">
                  {health.database.active_connections} / {health.database.connection_pool_size}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">WebSocket:</span>
                <span className="info-value">
                  {health.websocket.active_connections} / {health.websocket.max_connections} connections
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">API Requests:</span>
                <span className="info-value">{health.schwab_api.request_count_24h.toLocaleString()}/24h</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Health Score Visualization */}
      <div className="health-score-section">
        <h3>Overall Health Score</h3>
        <div className="score-visualization">
          <div className="score-circle">
            <svg viewBox="0 0 100 100" className="score-progress">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="rgba(255, 255, 255, 0.1)"
                strokeWidth="8"
              />
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke={getStatusColor(overallStatus)}
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${(healthScore / 100) * 251.2} 251.2`}
                transform="rotate(-90 50 50)"
              />
            </svg>
            <div className="score-text">
              <div className="score-number">{healthScore}%</div>
              <div className="score-label">Health Score</div>
            </div>
          </div>
          <div className="score-legend">
            <div className="legend-item">
              <div className="legend-color" style={{ backgroundColor: '#00d4aa' }}></div>
              <span>Healthy (90-100%)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ backgroundColor: '#ffb347' }}></div>
              <span>Warning (70-89%)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ backgroundColor: '#ff5555' }}></div>
              <span>Critical (&lt;70%)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealth;