/**
 * Analytics Dashboard Component
 * 
 * Main container for all analytics features, providing instrument selection
 * and comprehensive analytics data display.
 */

import React, { useState, useMemo } from 'react';
import { useAnalyticsHealth } from '../../hooks/useAnalytics';
import { MarketAnalysisSection } from './MarketAnalysisSection';
import { TechnicalIndicatorsSection } from './TechnicalIndicatorsSection';
import { PricePredictionSection } from './PricePredictionSection';
import { RiskMetricsSection } from './RiskMetricsSection';
import { VolumeProfileSection } from './VolumeProfileSection';
import { InstrumentSelector } from '../common/InstrumentSelector';
import { ErrorBoundary } from '../common/ErrorBoundary';
import './AnalyticsDashboard.css';

interface AnalyticsDashboardProps {
  defaultInstrumentId?: number;
  className?: string;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  defaultInstrumentId = 1,
  className = ''
}) => {
  const [selectedInstrumentId, setSelectedInstrumentId] = useState(defaultInstrumentId);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  
  const { data: healthData, error: healthError } = useAnalyticsHealth();

  const handleInstrumentChange = (instrumentId: number, symbol: string) => {
    setSelectedInstrumentId(instrumentId);
    setSelectedSymbol(symbol);
  };

  const isAnalyticsHealthy = useMemo(() => {
    if (!healthData) return true; // Assume healthy if no data yet
    return healthData.status === 'healthy' || healthData.status === 'ok';
  }, [healthData]);

  return (
    <div className={`analytics-dashboard ${className}`}>
      {/* Header Section */}
      <div className="analytics-dashboard__header">
        <div className="analytics-dashboard__title">
          <>
            <h1>Analytics Dashboard</h1>
            {healthError && (
              <div className="analytics-dashboard__health-error">
                Analytics services may be unavailable
              </div>
            )}
            {!isAnalyticsHealthy && healthData && (
              <div className="analytics-dashboard__health-warning">
                Analytics services are degraded
              </div>
            )}
          </>
        </div>
        
        <div className="analytics-dashboard__controls">
          <InstrumentSelector
            value={selectedInstrumentId}
            onChange={handleInstrumentChange}
            placeholder="Select instrument for analysis"
            className="analytics-dashboard__instrument-selector"
          />
        </div>
      </div>

      {/* Analytics Grid */}
      {selectedInstrumentId ? (
        <div className="analytics-dashboard__grid">
          {/* Row 1: Market Analysis and Technical Indicators */}
          <div className="analytics-dashboard__row">
            <ErrorBoundary fallback={<div className="analytics-error">Market Analysis Error</div>}>
              <div className="analytics-dashboard__section analytics-dashboard__section--half">
                <MarketAnalysisSection 
                  instrumentId={selectedInstrumentId}
                  symbol={selectedSymbol}
                />
              </div>
            </ErrorBoundary>
            
            <ErrorBoundary fallback={<div className="analytics-error">Technical Indicators Error</div>}>
              <div className="analytics-dashboard__section analytics-dashboard__section--half">
                <TechnicalIndicatorsSection 
                  instrumentId={selectedInstrumentId}
                  symbol={selectedSymbol}
                />
              </div>
            </ErrorBoundary>
          </div>

          {/* Row 2: Price Prediction and Risk Metrics */}
          <div className="analytics-dashboard__row">
            <ErrorBoundary fallback={<div className="analytics-error">Price Prediction Error</div>}>
              <div className="analytics-dashboard__section analytics-dashboard__section--two-thirds">
                <PricePredictionSection 
                  instrumentId={selectedInstrumentId}
                  symbol={selectedSymbol}
                />
              </div>
            </ErrorBoundary>
            
            <ErrorBoundary fallback={<div className="analytics-error">Risk Metrics Error</div>}>
              <div className="analytics-dashboard__section analytics-dashboard__section--one-third">
                <RiskMetricsSection 
                  instrumentId={selectedInstrumentId}
                  symbol={selectedSymbol}
                />
              </div>
            </ErrorBoundary>
          </div>

          {/* Row 3: Volume Profile */}
          <div className="analytics-dashboard__row">
            <ErrorBoundary fallback={<div className="analytics-error">Volume Profile Error</div>}>
              <div className="analytics-dashboard__section analytics-dashboard__section--full">
                <VolumeProfileSection 
                  instrumentId={selectedInstrumentId}
                  symbol={selectedSymbol}
                />
              </div>
            </ErrorBoundary>
          </div>
        </div>
      ) : (
        <div className="analytics-dashboard__empty">
          <div className="analytics-dashboard__empty-content">
            <div className="analytics-dashboard__empty-icon">📊</div>
            <h2>Analytics Dashboard</h2>
            <p>Select an instrument above to view comprehensive analytics data including:</p>
            <ul>
              <li>Market trend analysis and technical patterns</li>
              <li>Real-time technical indicators (RSI, MACD, Bollinger Bands)</li>
              <li>Machine learning price predictions</li>
              <li>Risk metrics and Value at Risk calculations</li>
              <li>Volume profile and market microstructure analysis</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};