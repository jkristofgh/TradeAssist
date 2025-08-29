/**
 * Technical Indicators Component
 * 
 * Displays interactive charts and data for various technical indicators
 * including RSI, MACD, Bollinger Bands, Moving Averages, and more.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './TechnicalIndicators.css';

interface TechnicalIndicator {
  type: string;
  timestamp: string;
  values: Record<string, number>;
  metadata: Record<string, any>;
}

interface TechnicalIndicatorsProps {
  instrumentId: number;
  analysisData: {
    technical_indicators: TechnicalIndicator[];
    trend_analysis: any;
  };
}

interface RealTimeIndicatorData {
  timestamp: string;
  instrument_id: number;
  instrument_symbol: string;
  indicators: TechnicalIndicator[];
}

const TechnicalIndicators: React.FC<TechnicalIndicatorsProps> = ({ 
  instrumentId, 
  analysisData 
}) => {
  const [realTimeData, setRealTimeData] = useState<RealTimeIndicatorData | null>(null);
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>([
    'rsi', 'macd', 'bollinger_bands', 'moving_average'
  ]);
  const [loading, setLoading] = useState<boolean>(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  // Available indicators for selection
  const availableIndicators = [
    { key: 'rsi', name: 'RSI', description: 'Relative Strength Index' },
    { key: 'macd', name: 'MACD', description: 'Moving Average Convergence Divergence' },
    { key: 'bollinger_bands', name: 'Bollinger Bands', description: 'Bollinger Bands' },
    { key: 'moving_average', name: 'Moving Averages', description: 'Simple Moving Averages' },
    { key: 'stochastic', name: 'Stochastic', description: 'Stochastic Oscillator' },
    { key: 'atr', name: 'ATR', description: 'Average True Range' },
    { key: 'adx', name: 'ADX', description: 'Average Directional Index' }
  ];

  // Fetch real-time indicators
  const fetchRealTimeIndicators = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `/api/v1/analytics/real-time-indicators/${instrumentId}`,
        {
          params: { indicators: selectedIndicators }
        }
      );
      setRealTimeData(response.data);
    } catch (error) {
      console.error('Failed to fetch real-time indicators:', error);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh) {
      fetchRealTimeIndicators();
      const interval = setInterval(fetchRealTimeIndicators, 30000); // 30 seconds
      return () => clearInterval(interval);
    }
  }, [instrumentId, selectedIndicators, autoRefresh]);

  // Toggle indicator selection
  const toggleIndicator = (indicatorKey: string) => {
    setSelectedIndicators(prev =>
      prev.includes(indicatorKey)
        ? prev.filter(key => key !== indicatorKey)
        : [...prev, indicatorKey]
    );
  };

  // Get indicator data by type
  const getIndicatorData = (type: string) => {
    // First check real-time data
    if (realTimeData) {
      const rtIndicator = realTimeData.indicators.find(ind => ind.type === type);
      if (rtIndicator) return rtIndicator;
    }

    // Fallback to analysis data
    return analysisData.technical_indicators.find(ind => ind.type === type);
  };

  // RSI Component
  const RSIIndicator: React.FC<{ indicator: TechnicalIndicator }> = ({ indicator }) => {
    const rsi = indicator.values.rsi || 50;
    const overbought = indicator.values.overbought || 70;
    const oversold = indicator.values.oversold || 30;

    const getRSIColor = (value: number) => {
      if (value >= overbought) return '#f44336';
      if (value <= oversold) return '#4caf50';
      return '#00d4ff';
    };

    const getRSIStatus = (value: number) => {
      if (value >= overbought) return 'Overbought';
      if (value <= oversold) return 'Oversold';
      return 'Normal';
    };

    return (
      <div className=\"indicator-card\">
        <div className=\"indicator-header\">
          <h3>RSI</h3>
          <div className=\"indicator-value\" style={{ color: getRSIColor(rsi) }}>
            {rsi.toFixed(1)}
          </div>
        </div>
        
        <div className=\"rsi-gauge\">
          <div className=\"rsi-track\">
            <div className=\"rsi-levels\">
              <div className=\"level oversold\" style={{ left: `${(oversold/100)*100}%` }}>
                {oversold}
              </div>
              <div className=\"level overbought\" style={{ left: `${(overbought/100)*100}%` }}>
                {overbought}
              </div>
            </div>
            <div 
              className=\"rsi-needle\" 
              style={{ 
                left: `${rsi}%`, 
                backgroundColor: getRSIColor(rsi)
              }}
            ></div>
          </div>
        </div>

        <div className=\"indicator-status\">
          <span className={`status-badge ${getRSIStatus(rsi).toLowerCase()}`}>
            {getRSIStatus(rsi)}
          </span>
        </div>

        <div className=\"indicator-details\">
          <div className=\"detail-item\">
            <span className=\"label\">Period:</span>
            <span className=\"value\">{indicator.metadata.period || 14}</span>
          </div>
        </div>
      </div>
    );
  };

  // MACD Component  
  const MACDIndicator: React.FC<{ indicator: TechnicalIndicator }> = ({ indicator }) => {
    const macd = indicator.values.macd || 0;
    const signal = indicator.values.signal || 0;
    const histogram = indicator.values.histogram || 0;

    const getMACDSignal = () => {
      if (macd > signal && histogram > 0) return 'Bullish';
      if (macd < signal && histogram < 0) return 'Bearish';
      return 'Neutral';
    };

    const getSignalColor = (signal: string) => {
      switch (signal) {
        case 'Bullish': return '#4caf50';
        case 'Bearish': return '#f44336';
        default: return '#ff9800';
      }
    };

    return (
      <div className=\"indicator-card\">
        <div className=\"indicator-header\">
          <h3>MACD</h3>
          <div className=\"indicator-value\">
            {macd.toFixed(4)}
          </div>
        </div>

        <div className=\"macd-display\">
          <div className=\"macd-lines\">
            <div className=\"macd-line\">
              <span className=\"line-label\">MACD:</span>
              <span className=\"line-value macd\">{macd.toFixed(4)}</span>
            </div>
            <div className=\"macd-line\">
              <span className=\"line-label\">Signal:</span>
              <span className=\"line-value signal\">{signal.toFixed(4)}</span>
            </div>
            <div className=\"macd-line\">
              <span className=\"line-label\">Histogram:</span>
              <span className={`line-value histogram ${histogram >= 0 ? 'positive' : 'negative'}`}>
                {histogram.toFixed(4)}
              </span>
            </div>
          </div>
        </div>

        <div className=\"indicator-status\">
          <span 
            className={`status-badge ${getMACDSignal().toLowerCase()}`}
            style={{ backgroundColor: getSignalColor(getMACDSignal()) }}
          >
            {getMACDSignal()}
          </span>
        </div>

        <div className=\"indicator-details\">
          <div className=\"detail-item\">
            <span className=\"label\">Fast:</span>
            <span className=\"value\">{indicator.metadata.fast || 12}</span>
          </div>
          <div className=\"detail-item\">
            <span className=\"label\">Slow:</span>
            <span className=\"value\">{indicator.metadata.slow || 26}</span>
          </div>
          <div className=\"detail-item\">
            <span className=\"label\">Signal:</span>
            <span className=\"value\">{indicator.metadata.signal || 9}</span>
          </div>
        </div>
      </div>
    );
  };

  // Bollinger Bands Component
  const BollingerBandsIndicator: React.FC<{ indicator: TechnicalIndicator }> = ({ indicator }) => {
    const upperBand = indicator.values.upper_band || 0;
    const middleBand = indicator.values.middle_band || 0;
    const lowerBand = indicator.values.lower_band || 0;
    const bandwidth = indicator.values.bandwidth || 0;
    const currentPrice = analysisData.trend_analysis.current_price;

    const getBandPosition = () => {
      const position = (currentPrice - lowerBand) / (upperBand - lowerBand);
      if (position > 0.8) return 'Near Upper Band';
      if (position < 0.2) return 'Near Lower Band';
      return 'Middle Range';
    };

    return (
      <div className=\"indicator-card\">
        <div className=\"indicator-header\">
          <h3>Bollinger Bands</h3>
          <div className=\"indicator-value\">
            {bandwidth.toFixed(2)}%
          </div>
        </div>

        <div className=\"bollinger-display\">
          <div className=\"band-line\">
            <span className=\"band-label upper\">Upper:</span>
            <span className=\"band-value\">{upperBand.toFixed(4)}</span>
          </div>
          <div className=\"band-line\">
            <span className=\"band-label middle\">Middle:</span>
            <span className=\"band-value\">{middleBand.toFixed(4)}</span>
          </div>
          <div className=\"band-line\">
            <span className=\"band-label lower\">Lower:</span>
            <span className=\"band-value\">{lowerBand.toFixed(4)}</span>
          </div>
        </div>

        <div className=\"price-position\">
          <div className=\"position-indicator\">
            <div className=\"position-track\">
              <div 
                className=\"position-marker\"
                style={{
                  left: `${Math.min(Math.max((currentPrice - lowerBand) / (upperBand - lowerBand) * 100, 0), 100)}%`
                }}
              ></div>
            </div>
            <div className=\"position-labels\">
              <span className=\"lower-label\">{lowerBand.toFixed(4)}</span>
              <span className=\"upper-label\">{upperBand.toFixed(4)}</span>
            </div>
          </div>
          <div className=\"position-status\">{getBandPosition()}</div>
        </div>

        <div className=\"indicator-details\">
          <div className=\"detail-item\">
            <span className=\"label\">Period:</span>
            <span className=\"value\">{indicator.metadata.period || 20}</span>
          </div>
          <div className=\"detail-item\">
            <span className=\"label\">Std Dev:</span>
            <span className=\"value\">{indicator.metadata.std_dev || 2}</span>
          </div>
        </div>
      </div>
    );
  };

  // Moving Averages Component
  const MovingAveragesIndicator: React.FC<{ indicator: TechnicalIndicator }> = ({ indicator }) => {
    const periods = indicator.metadata.periods || [5, 10, 20, 50, 200];
    const currentPrice = analysisData.trend_analysis.current_price;

    const getTrendDirection = (ma: number) => {
      if (currentPrice > ma) return 'above';
      return 'below';
    };

    return (
      <div className=\"indicator-card\">
        <div className=\"indicator-header\">
          <h3>Moving Averages</h3>
          <div className=\"indicator-value\">
            {periods.length} MAs
          </div>
        </div>

        <div className=\"ma-list\">
          {periods.map((period: number) => {
            const maKey = `ma_${period}`;
            const maValue = indicator.values[maKey];
            if (!maValue) return null;

            return (
              <div key={period} className=\"ma-item\">
                <div className=\"ma-period\">MA{period}</div>
                <div className=\"ma-value\">{maValue.toFixed(4)}</div>
                <div className={`ma-trend ${getTrendDirection(maValue)}`}>
                  {getTrendDirection(maValue) === 'above' ? '↑' : '↓'}
                </div>
              </div>
            );
          })}
        </div>

        <div className=\"ma-summary\">
          <div className=\"current-price\">
            Current: {currentPrice.toFixed(4)}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className=\"technical-indicators\">
      <div className=\"indicators-header\">
        <div className=\"indicator-selector\">
          <h3>Select Indicators</h3>
          <div className=\"indicator-checkboxes\">
            {availableIndicators.map((indicator) => (
              <label key={indicator.key} className=\"indicator-checkbox\">
                <input
                  type=\"checkbox\"
                  checked={selectedIndicators.includes(indicator.key)}
                  onChange={() => toggleIndicator(indicator.key)}
                />
                <span className=\"checkbox-label\">{indicator.name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className=\"refresh-controls\">
          <label className=\"auto-refresh-toggle\">
            <input
              type=\"checkbox\"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            <span>Auto Refresh</span>
          </label>
          <button
            onClick={fetchRealTimeIndicators}
            disabled={loading}
            className=\"manual-refresh-btn\"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className=\"indicators-grid\">
        {selectedIndicators.map((indicatorType) => {
          const indicator = getIndicatorData(indicatorType);
          if (!indicator) return null;

          switch (indicatorType) {
            case 'rsi':
              return <RSIIndicator key={indicatorType} indicator={indicator} />;
            case 'macd':
              return <MACDIndicator key={indicatorType} indicator={indicator} />;
            case 'bollinger_bands':
              return <BollingerBandsIndicator key={indicatorType} indicator={indicator} />;
            case 'moving_average':
              return <MovingAveragesIndicator key={indicatorType} indicator={indicator} />;
            default:
              return (
                <div key={indicatorType} className=\"indicator-card generic\">
                  <div className=\"indicator-header\">
                    <h3>{indicatorType.toUpperCase()}</h3>
                  </div>
                  <div className=\"indicator-values\">
                    {Object.entries(indicator.values).map(([key, value]) => (
                      <div key={key} className=\"value-item\">
                        <span className=\"key\">{key}:</span>
                        <span className=\"value\">{typeof value === 'number' ? value.toFixed(4) : value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
          }
        })}
      </div>

      {selectedIndicators.length === 0 && (
        <div className=\"no-indicators\">
          <div className=\"empty-icon\">📈</div>
          <h3>No Indicators Selected</h3>
          <p>Select one or more technical indicators from the list above to view their analysis.</p>
        </div>
      )}

      <div className=\"indicators-footer\">
        <div className=\"last-update\">
          {realTimeData && (
            <span>Real-time data: {new Date(realTimeData.timestamp).toLocaleString()}</span>
          )}
        </div>
        <div className=\"data-source\">
          <span className={`source-indicator ${realTimeData ? 'real-time' : 'cached'}`}>
            ● {realTimeData ? 'Real-time' : 'Cached'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default TechnicalIndicators;