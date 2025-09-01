/**
 * Risk Metrics Section Component
 * 
 * Displays comprehensive risk analysis including VaR, volatility,
 * Sharpe ratio, and other risk metrics.
 */

import React from 'react';
import { useRiskMetrics, useVarCalculation } from '../../hooks/useAnalytics';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import './RiskMetricsSection.css';

interface RiskMetricsSectionProps {
  instrumentId: number;
  symbol: string;
  className?: string;
}

export const RiskMetricsSection: React.FC<RiskMetricsSectionProps> = ({
  instrumentId,
  symbol,
  className = ''
}) => {
  const { data: riskMetrics, isLoading: isLoadingRisk, error: riskError, refetch: refetchRisk } = useRiskMetrics(instrumentId, {
    portfolioValue: 100000,
    confidenceLevel: 0.95,
    timeframe: 'day'
  });

  const { data: varData, isLoading: isLoadingVar, error: varError } = useVarCalculation(instrumentId, {
    portfolioValue: 100000,
    confidenceLevel: 0.95,
    timeframe: 'day'
  });

  const isLoading = isLoadingRisk || isLoadingVar;
  const error = riskError || varError;

  if (error) {
    return (
      <div className={`risk-metrics-section ${className}`}>
        <div className="risk-metrics-section__header">
          <h3 className="risk-metrics-section__title">Risk Metrics</h3>
        </div>
        <ErrorAlert 
          message="Failed to load risk metrics" 
          error={error}
          onRetry={() => refetchRisk()}
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`risk-metrics-section ${className}`}>
        <div className="risk-metrics-section__header">
          <h3 className="risk-metrics-section__title">Risk Metrics</h3>
        </div>
        <div className="risk-metrics-section__loading">
          <LoadingSpinner size="medium" />
          <p>Calculating risk metrics...</p>
        </div>
      </div>
    );
  }

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(Math.abs(value));
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatNumber = (value: number): string => {
    return value.toFixed(4);
  };

  const getRiskLevel = (value: number, type: 'volatility' | 'var'): { level: string; color: string } => {
    if (type === 'volatility') {
      if (value < 0.1) return { level: 'Low', color: 'risk-low' };
      if (value < 0.2) return { level: 'Medium', color: 'risk-medium' };
      return { level: 'High', color: 'risk-high' };
    } else { // VaR
      const percentage = Math.abs(value) * 100;
      if (percentage < 2) return { level: 'Low', color: 'risk-low' };
      if (percentage < 5) return { level: 'Medium', color: 'risk-medium' };
      return { level: 'High', color: 'risk-high' };
    }
  };

  return (
    <div className={`risk-metrics-section ${className}`}>
      <div className="risk-metrics-section__header">
        <h3 className="risk-metrics-section__title">
          Risk Metrics - {symbol}
        </h3>
        {riskMetrics?.timestamp && (
          <div className="risk-metrics-section__timestamp">
            Updated: {new Date(riskMetrics.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
      
      <div className="risk-metrics-section__content">
        {/* Value at Risk */}
        {riskMetrics && (
          <div className="risk-metric-card">
            <div className="risk-metric-card__header">
              <h4 className="risk-metric-card__title">Value at Risk</h4>
              <div className={`risk-level ${getRiskLevel(riskMetrics.var95, 'var').color}`}>
                {getRiskLevel(riskMetrics.var95, 'var').level}
              </div>
            </div>
            <div className="risk-metric-card__body">
              <div className="var-metrics">
                <div className="var-metric">
                  <div className="var-metric__label">95% VaR (1 day)</div>
                  <div className="var-metric__value var-metric__value--95">
                    {formatCurrency(riskMetrics.var95)}
                  </div>
                </div>
                <div className="var-metric">
                  <div className="var-metric__label">99% VaR (1 day)</div>
                  <div className="var-metric__value var-metric__value--99">
                    {formatCurrency(riskMetrics.var99)}
                  </div>
                </div>
              </div>
              {varData && (
                <div className="var-details">
                  <div className="var-detail-item">
                    <span className="var-detail-label">Expected Shortfall:</span>
                    <span className="var-detail-value">{formatCurrency(varData.expectedShortfall)}</span>
                  </div>
                  <div className="var-detail-item">
                    <span className="var-detail-label">Methodology:</span>
                    <span className="var-detail-value">{varData.methodology}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Volatility */}
        {riskMetrics && (
          <div className="risk-metric-card">
            <div className="risk-metric-card__header">
              <h4 className="risk-metric-card__title">Volatility</h4>
              <div className={`risk-level ${getRiskLevel(riskMetrics.volatility, 'volatility').color}`}>
                {getRiskLevel(riskMetrics.volatility, 'volatility').level}
              </div>
            </div>
            <div className="risk-metric-card__body">
              <div className="volatility-display">
                <div className="volatility-display__value">
                  {formatPercentage(riskMetrics.volatility)}
                </div>
                <div className="volatility-display__label">Annualized Volatility</div>
              </div>
            </div>
          </div>
        )}

        {/* Performance Metrics */}
        {riskMetrics && (
          <div className="risk-metric-card">
            <div className="risk-metric-card__header">
              <h4 className="risk-metric-card__title">Performance</h4>
            </div>
            <div className="risk-metric-card__body">
              <div className="performance-metrics">
                {riskMetrics.sharpeRatio && (
                  <div className="performance-metric">
                    <div className="performance-metric__label">Sharpe Ratio</div>
                    <div className={`performance-metric__value ${
                      riskMetrics.sharpeRatio > 1 ? 'performance-metric__value--good' :
                      riskMetrics.sharpeRatio > 0 ? 'performance-metric__value--neutral' :
                      'performance-metric__value--poor'
                    }`}>
                      {formatNumber(riskMetrics.sharpeRatio)}
                    </div>
                  </div>
                )}
                
                <div className="performance-metric">
                  <div className="performance-metric__label">Max Drawdown</div>
                  <div className="performance-metric__value performance-metric__value--poor">
                    {formatPercentage(riskMetrics.maxDrawdown)}
                  </div>
                </div>

                {riskMetrics.beta && (
                  <div className="performance-metric">
                    <div className="performance-metric__label">Beta</div>
                    <div className={`performance-metric__value ${
                      Math.abs(riskMetrics.beta - 1) < 0.2 ? 'performance-metric__value--neutral' :
                      riskMetrics.beta > 1.2 ? 'performance-metric__value--poor' :
                      'performance-metric__value--good'
                    }`}>
                      {formatNumber(riskMetrics.beta)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Risk Summary */}
        <div className="risk-summary">
          <h4 className="section-subtitle">Risk Assessment</h4>
          <div className="risk-summary__content">
            {riskMetrics && (
              <>
                <p className="risk-summary__text">
                  Based on historical data from the past {riskMetrics.timeframe}, this instrument shows{' '}
                  <strong className={getRiskLevel(riskMetrics.volatility, 'volatility').color}>
                    {getRiskLevel(riskMetrics.volatility, 'volatility').level.toLowerCase()} volatility
                  </strong>{' '}
                  with a 95% VaR of {formatCurrency(riskMetrics.var95)} over a 1-day period.
                </p>
                
                {riskMetrics.sharpeRatio && (
                  <p className="risk-summary__text">
                    The Sharpe ratio of {formatNumber(riskMetrics.sharpeRatio)} indicates{' '}
                    {riskMetrics.sharpeRatio > 1 ? 'excellent' :
                     riskMetrics.sharpeRatio > 0.5 ? 'good' :
                     riskMetrics.sharpeRatio > 0 ? 'moderate' : 'poor'} risk-adjusted returns.
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};