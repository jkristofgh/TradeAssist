/**
 * Market Analytics Dashboard Component
 * 
 * Main dashboard for advanced market analytics including technical indicators,
 * predictive models, risk analysis, and market sentiment.
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './MarketAnalytics.css';
import TechnicalIndicators from './TechnicalIndicators';
import PredictiveModels from './PredictiveModels';
import RiskAnalysis from './RiskAnalysis';
import MarketSentiment from './MarketSentiment';
import VolumeProfile from './VolumeProfile';

interface Instrument {
  id: number;
  symbol: string;
  name: string;
  type: string;
}

interface MarketAnalysisData {
  timestamp: string;
  instrument_id: number;
  instrument_symbol: string;
  lookback_hours: number;
  technical_indicators: TechnicalIndicator[];
  trend_analysis: TrendAnalysis;
  volatility_metrics: VolatilityMetrics;
  support_resistance: SupportResistance;
  pattern_signals: PatternSignal[];
}

interface TechnicalIndicator {
  type: string;
  timestamp: string;
  values: Record<string, number>;
  metadata: Record<string, any>;
}

interface TrendAnalysis {
  short_term: string;
  medium_term: string;
  long_term: string;
  trend_strength_20d: number;
  current_price: number;
  ma_20: number;
  ma_50: number;
}

interface VolatilityMetrics {
  volatility_annualized: number;
  atr_percent: number;
  daily_volatility: number;
  volatility_rank: number;
}

interface SupportResistance {
  support: number[];
  resistance: number[];
}

interface PatternSignal {
  pattern: string;
  signal: string;
  confidence: number;
  description: string;
}

const MarketAnalytics: React.FC = () => {
  const [selectedInstrument, setSelectedInstrument] = useState<number>(1);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [analysisData, setAnalysisData] = useState<MarketAnalysisData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<number>(60000); // 1 minute
  const [lookbackHours, setLookbackHours] = useState<number>(24);
  const [activeTab, setActiveTab] = useState<string>('indicators');

  // Load instruments on component mount
  useEffect(() => {
    const fetchInstruments = async () => {
      try {
        const response = await axios.get('/api/instruments');
        setInstruments(response.data);
      } catch (err) {
        console.error('Failed to fetch instruments:', err);
        setError('Failed to load instruments');
      }
    };

    fetchInstruments();
  }, []);

  // Fetch market analysis data
  const fetchMarketAnalysis = useCallback(async () => {
    if (!selectedInstrument) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `/api/v1/analytics/market-analysis/${selectedInstrument}?lookback_hours=${lookbackHours}`
      );
      setAnalysisData(response.data);
    } catch (err: any) {
      console.error('Failed to fetch market analysis:', err);
      setError(err.response?.data?.detail || 'Failed to fetch market analysis');
    } finally {
      setLoading(false);
    }
  }, [selectedInstrument, lookbackHours]);

  // Auto-refresh data
  useEffect(() => {
    fetchMarketAnalysis();

    const interval = setInterval(fetchMarketAnalysis, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchMarketAnalysis, refreshInterval]);

  const handleInstrumentChange = (instrumentId: number) => {
    setSelectedInstrument(instrumentId);
    setAnalysisData(null); // Clear previous data
  };

  const handleRefreshIntervalChange = (interval: number) => {
    setRefreshInterval(interval);
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'bullish': return '#4CAF50';
      case 'bearish': return '#F44336';
      case 'sideways': return '#FF9800';
      default: return '#757575';
    }
  };

  const getVolatilityLevel = (rank: number) => {
    if (rank < 1) return 'Very Low';
    if (rank < 2) return 'Low';
    if (rank < 3) return 'Medium';
    if (rank < 4) return 'High';
    return 'Very High';
  };

  return (
    <div className=\"market-analytics-dashboard\">
      <div className=\"analytics-header\">
        <div className=\"header-controls\">
          <div className=\"instrument-selector\">
            <label htmlFor=\"instrument-select\">Instrument:</label>
            <select
              id=\"instrument-select\"
              value={selectedInstrument}
              onChange={(e) => handleInstrumentChange(Number(e.target.value))}
              className=\"instrument-dropdown\"
            >
              {instruments.map((instrument) => (
                <option key={instrument.id} value={instrument.id}>
                  {instrument.symbol} - {instrument.name}
                </option>
              ))}
            </select>
          </div>

          <div className=\"lookback-selector\">
            <label htmlFor=\"lookback-select\">Lookback:</label>
            <select
              id=\"lookback-select\"
              value={lookbackHours}
              onChange={(e) => setLookbackHours(Number(e.target.value))}
              className=\"lookback-dropdown\"
            >
              <option value={1}>1 Hour</option>
              <option value={4}>4 Hours</option>
              <option value={24}>24 Hours</option>
              <option value={72}>3 Days</option>
              <option value={168}>1 Week</option>
            </select>
          </div>

          <div className=\"refresh-selector\">
            <label htmlFor=\"refresh-select\">Auto Refresh:</label>
            <select
              id=\"refresh-select\"
              value={refreshInterval}
              onChange={(e) => handleRefreshIntervalChange(Number(e.target.value))}
              className=\"refresh-dropdown\"
            >
              <option value={30000}>30 seconds</option>
              <option value={60000}>1 minute</option>
              <option value={300000}>5 minutes</option>
              <option value={0}>Manual</option>
            </select>
          </div>

          <button
            onClick={fetchMarketAnalysis}
            disabled={loading}
            className=\"refresh-button\"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {error && (
          <div className=\"error-message\">
            <span className=\"error-icon\">⚠️</span>
            {error}
          </div>
        )}

        {analysisData && (
          <div className=\"analysis-summary\">
            <div className=\"summary-card\">
              <h3>Current Price</h3>
              <div className=\"price-display\">
                ${analysisData.trend_analysis.current_price.toFixed(4)}
              </div>
            </div>

            <div className=\"summary-card\">
              <h3>Short-term Trend</h3>
              <div 
                className=\"trend-indicator\"
                style={{ color: getTrendColor(analysisData.trend_analysis.short_term) }}
              >
                {analysisData.trend_analysis.short_term.toUpperCase()}
              </div>
              <div className=\"trend-strength\">
                Strength: {analysisData.trend_analysis.trend_strength_20d.toFixed(2)}%
              </div>
            </div>

            <div className=\"summary-card\">
              <h3>Volatility</h3>
              <div className=\"volatility-display\">
                {(analysisData.volatility_metrics.volatility_annualized * 100).toFixed(1)}%
              </div>
              <div className=\"volatility-level\">
                {getVolatilityLevel(analysisData.volatility_metrics.volatility_rank)}
              </div>
            </div>

            <div className=\"summary-card\">
              <h3>Support/Resistance</h3>
              <div className=\"support-resistance\">
                <div className=\"resistance-levels\">
                  R: {analysisData.support_resistance.resistance.slice(0, 2).map(r => r.toFixed(4)).join(', ')}
                </div>
                <div className=\"support-levels\">
                  S: {analysisData.support_resistance.support.slice(0, 2).map(s => s.toFixed(4)).join(', ')}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className=\"analytics-tabs\">
        <button
          className={`tab-button ${activeTab === 'indicators' ? 'active' : ''}`}
          onClick={() => setActiveTab('indicators')}
        >
          Technical Indicators
        </button>
        <button
          className={`tab-button ${activeTab === 'predictions' ? 'active' : ''}`}
          onClick={() => setActiveTab('predictions')}
        >
          ML Predictions
        </button>
        <button
          className={`tab-button ${activeTab === 'risk' ? 'active' : ''}`}
          onClick={() => setActiveTab('risk')}
        >
          Risk Analysis
        </button>
        <button
          className={`tab-button ${activeTab === 'sentiment' ? 'active' : ''}`}
          onClick={() => setActiveTab('sentiment')}
        >
          Market Sentiment
        </button>
        <button
          className={`tab-button ${activeTab === 'volume' ? 'active' : ''}`}
          onClick={() => setActiveTab('volume')}
        >
          Volume Profile
        </button>
      </div>

      <div className=\"analytics-content\">
        {loading && (
          <div className=\"loading-spinner\">
            <div className=\"spinner\"></div>
            <p>Loading market analysis...</p>
          </div>
        )}

        {!loading && analysisData && (
          <>
            {activeTab === 'indicators' && (
              <TechnicalIndicators
                instrumentId={selectedInstrument}
                analysisData={analysisData}
              />
            )}

            {activeTab === 'predictions' && (
              <PredictiveModels
                instrumentId={selectedInstrument}
                currentPrice={analysisData.trend_analysis.current_price}
              />
            )}

            {activeTab === 'risk' && (
              <RiskAnalysis
                instrumentId={selectedInstrument}
                currentPrice={analysisData.trend_analysis.current_price}
                volatilityMetrics={analysisData.volatility_metrics}
              />
            )}

            {activeTab === 'sentiment' && (
              <MarketSentiment
                instrumentId={selectedInstrument}
                patternSignals={analysisData.pattern_signals}
              />
            )}

            {activeTab === 'volume' && (
              <VolumeProfile
                instrumentId={selectedInstrument}
                lookbackHours={lookbackHours}
              />
            )}
          </>
        )}

        {!loading && !analysisData && !error && (
          <div className=\"empty-state\">
            <div className=\"empty-icon\">📊</div>
            <h3>Market Analysis</h3>
            <p>Select an instrument and click refresh to view detailed market analysis.</p>
          </div>
        )}
      </div>

      {analysisData && (
        <div className=\"pattern-alerts\">
          <h3>Pattern Signals</h3>
          <div className=\"pattern-list\">
            {analysisData.pattern_signals.length > 0 ? (
              analysisData.pattern_signals.map((pattern, index) => (
                <div
                  key={index}
                  className={`pattern-signal ${pattern.signal}`}
                >
                  <div className=\"pattern-name\">{pattern.pattern.replace(/_/g, ' ').toUpperCase()}</div>
                  <div className=\"pattern-signal-type\">{pattern.signal.toUpperCase()}</div>
                  <div className=\"pattern-confidence\">
                    Confidence: {(pattern.confidence * 100).toFixed(0)}%
                  </div>
                  <div className=\"pattern-description\">{pattern.description}</div>
                </div>
              ))
            ) : (
              <div className=\"no-patterns\">
                No significant patterns detected in the current timeframe.
              </div>
            )}
          </div>
        </div>
      )}

      <div className=\"analytics-footer\">
        <div className=\"last-updated\">
          {analysisData && (
            <span>
              Last updated: {new Date(analysisData.timestamp).toLocaleString()}
            </span>
          )}
        </div>
        <div className=\"data-quality\">
          <span className=\"data-status healthy\">● Live Data</span>
        </div>
      </div>
    </div>
  );
};

export default MarketAnalytics;