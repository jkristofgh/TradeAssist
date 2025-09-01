/**
 * Performance Metrics Dashboard Component - Phase 3
 * 
 * Displays comprehensive API performance metrics including response times,
 * error rates, cache hit rates, and alert status.
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardHeader, 
  CardContent, 
  CardTitle 
} from '../common/Card';
import { Alert, AlertDescription } from '../common/Alert';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';

interface ResponseTimeStats {
  mean: number;
  median: number;
  p95: number;
  p99: number;
  min: number;
  max: number;
}

interface CacheStats {
  hits: number;
  misses: number;
  hit_rate: number;
}

interface GlobalStats {
  total_requests: number;
  error_count: number;
  error_rate: number;
  response_times: ResponseTimeStats;
  cache_statistics: CacheStats;
  uptime_seconds: number;
}

interface EndpointStats {
  [endpoint: string]: GlobalStats;
}

interface PerformanceData {
  global_statistics: GlobalStats;
  endpoint_statistics: EndpointStats;
}

interface MonitoringConfig {
  performance_tracking_enabled: boolean;
  error_tracking_enabled: boolean;
  alerting_enabled: boolean;
  sample_rate: number;
}

interface PerformanceMetricsResponse {
  success: boolean;
  timestamp: string;
  performance_data: PerformanceData;
  monitoring_config: MonitoringConfig;
}

const PerformanceMetrics: React.FC = () => {
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [monitoringConfig, setMonitoringConfig] = useState<MonitoringConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  const fetchPerformanceData = async () => {
    try {
      const response = await fetch('/api/health/performance/statistics');
      const data: PerformanceMetricsResponse = await response.json();
      
      if (data.success) {
        setPerformanceData(data.performance_data);
        setMonitoringConfig(data.monitoring_config);
        setLastUpdated(new Date().toLocaleTimeString());
        setError(null);
      } else {
        throw new Error('Failed to fetch performance data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const resetStatistics = async () => {
    try {
      const response = await fetch('/api/health/performance/reset', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        // Refresh data after reset
        await fetchPerformanceData();
      } else {
        throw new Error('Failed to reset statistics');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset statistics');
    }
  };

  useEffect(() => {
    fetchPerformanceData();
    
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(fetchPerformanceData, 30000); // Refresh every 30 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const formatNumber = (num: number, decimals: number = 2): string => {
    return num.toLocaleString(undefined, { 
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals 
    });
  };

  const getErrorRateBadgeColor = (errorRate: number): string => {
    if (errorRate < 0.01) return 'success';
    if (errorRate < 0.05) return 'warning';
    return 'destructive';
  };

  const getCacheHitRateBadgeColor = (hitRate: number): string => {
    if (hitRate > 0.8) return 'success';
    if (hitRate > 0.6) return 'warning';
    return 'destructive';
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4">Loading performance data...</div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertDescription>
              Error loading performance data: {error}
            </AlertDescription>
          </Alert>
          <Button 
            onClick={fetchPerformanceData} 
            className="mt-4"
          >
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!performanceData || !monitoringConfig) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4">No performance data available</div>
        </CardContent>
      </Card>
    );
  }

  const globalStats = performanceData.global_statistics;
  const endpointStats = performanceData.endpoint_statistics;

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Performance Metrics</h2>
          <p className="text-sm text-gray-500 mt-1">
            Last updated: {lastUpdated}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={autoRefresh ? "default" : "outline"}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? "Auto-refresh: ON" : "Auto-refresh: OFF"}
          </Button>
          <Button onClick={fetchPerformanceData}>
            Refresh Now
          </Button>
          <Button 
            variant="destructive" 
            onClick={resetStatistics}
          >
            Reset Statistics
          </Button>
        </div>
      </div>

      {/* Monitoring Configuration Status */}
      <Card>
        <CardHeader>
          <CardTitle>Monitoring Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-sm text-gray-500">Performance Tracking</div>
              <Badge variant={monitoringConfig.performance_tracking_enabled ? "success" : "destructive"}>
                {monitoringConfig.performance_tracking_enabled ? "Enabled" : "Disabled"}
              </Badge>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Error Tracking</div>
              <Badge variant={monitoringConfig.error_tracking_enabled ? "success" : "destructive"}>
                {monitoringConfig.error_tracking_enabled ? "Enabled" : "Disabled"}
              </Badge>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Alerting</div>
              <Badge variant={monitoringConfig.alerting_enabled ? "success" : "secondary"}>
                {monitoringConfig.alerting_enabled ? "Enabled" : "Disabled"}
              </Badge>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Sample Rate</div>
              <div className="font-medium">{(monitoringConfig.sample_rate * 100).toFixed(0)}%</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Global Statistics */}
      <Card>
        <CardHeader>
          <CardTitle>Global Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {globalStats.total_requests.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Total Requests</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {globalStats.error_count.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Total Errors</div>
            </div>
            <div className="text-center">
              <Badge variant={getErrorRateBadgeColor(globalStats.error_rate)} className="text-lg px-3 py-1">
                {formatNumber(globalStats.error_rate * 100, 2)}%
              </Badge>
              <div className="text-sm text-gray-500 mt-1">Error Rate</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {formatDuration(globalStats.uptime_seconds)}
              </div>
              <div className="text-sm text-gray-500">Uptime</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Response Time Statistics */}
      <Card>
        <CardHeader>
          <CardTitle>Response Time Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
            <div className="text-center">
              <div className="text-xl font-bold">
                {formatNumber(globalStats.response_times.mean)}ms
              </div>
              <div className="text-sm text-gray-500">Mean</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold">
                {formatNumber(globalStats.response_times.median)}ms
              </div>
              <div className="text-sm text-gray-500">Median</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold">
                {formatNumber(globalStats.response_times.p95)}ms
              </div>
              <div className="text-sm text-gray-500">95th Percentile</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold">
                {formatNumber(globalStats.response_times.p99)}ms
              </div>
              <div className="text-sm text-gray-500">99th Percentile</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-green-600">
                {formatNumber(globalStats.response_times.min)}ms
              </div>
              <div className="text-sm text-gray-500">Min</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-red-600">
                {formatNumber(globalStats.response_times.max)}ms
              </div>
              <div className="text-sm text-gray-500">Max</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cache Statistics */}
      <Card>
        <CardHeader>
          <CardTitle>Cache Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {globalStats.cache_statistics.hits.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Cache Hits</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {globalStats.cache_statistics.misses.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Cache Misses</div>
            </div>
            <div className="text-center">
              <Badge variant={getCacheHitRateBadgeColor(globalStats.cache_statistics.hit_rate)} className="text-lg px-3 py-1">
                {formatNumber(globalStats.cache_statistics.hit_rate * 100, 1)}%
              </Badge>
              <div className="text-sm text-gray-500 mt-1">Hit Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top Endpoints by Request Count */}
      <Card>
        <CardHeader>
          <CardTitle>Endpoint Performance</CardTitle>
        </CardHeader>
        <CardContent>
          {Object.keys(endpointStats).length === 0 ? (
            <div className="text-center py-4 text-gray-500">
              No endpoint-specific statistics available
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(endpointStats)
                .sort(([, a], [, b]) => b.total_requests - a.total_requests)
                .slice(0, 10)
                .map(([endpoint, stats]) => (
                  <div 
                    key={endpoint} 
                    className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="font-medium text-sm">{endpoint}</div>
                      <div className="text-xs text-gray-500">
                        {stats.total_requests.toLocaleString()} requests
                      </div>
                    </div>
                    <div className="flex gap-4 text-sm">
                      <div className="text-center">
                        <div className="font-medium">
                          {formatNumber(stats.response_times?.mean || 0)}ms
                        </div>
                        <div className="text-xs text-gray-500">Avg Response</div>
                      </div>
                      <div className="text-center">
                        <Badge variant={getErrorRateBadgeColor(stats.error_rate)} size="sm">
                          {formatNumber(stats.error_rate * 100, 1)}%
                        </Badge>
                        <div className="text-xs text-gray-500">Error Rate</div>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PerformanceMetrics;