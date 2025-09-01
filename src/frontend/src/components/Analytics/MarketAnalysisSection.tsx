/**
 * Market Analysis Section Component
 * 
 * Displays comprehensive market analysis including trend detection,
 * technical patterns, support/resistance levels, and key indicators.
 */

import React from 'react';
import { useMarketAnalysis } from '../../hooks/useAnalytics';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import './MarketAnalysisSection.css';

interface MarketAnalysisSectionProps {
  instrumentId: number;
  symbol: string;
  className?: string;
}

export const MarketAnalysisSection: React.FC<MarketAnalysisSectionProps> = ({
  instrumentId,
  symbol,
  className = ''
}) => {
  const { data: analysis, isLoading, error, refetch } = useMarketAnalysis(instrumentId, {
    indicators: ['RSI', 'MACD', 'BOLLINGER_BANDS'],
    includePatterns: true,
    timeframe: 'day',
    lookbackPeriod: 30
  });

  if (error) {
    return (
      <div className={`market-analysis-section ${className}`}>
        <div className="market-analysis-section__header">
          <h3 className="market-analysis-section__title">Market Analysis</h3>
        </div>
        <ErrorAlert 
          message="Failed to load market analysis" 
          error={error}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`market-analysis-section ${className}`}>
        <div className="market-analysis-section__header">
          <h3 className="market-analysis-section__title">Market Analysis</h3>
        </div>
        <div className="market-analysis-section__loading">
          <LoadingSpinner size="medium" />
          <p>Analyzing market data...</p>
        </div>
      </div>
    );
  }

  const getTrendIcon = (trend: string) => {
    switch (trend?.toLowerCase()) {
      case 'bullish':
        return '📈';
      case 'bearish':
        return '📉';
      case 'neutral':
      case 'sideways':
        return '➡️';
      default:
        return '❓';
    }
  };

  const getTrendColor = (trend: string): string => {
    switch (trend?.toLowerCase()) {
      case 'bullish':
        return 'trend-bullish';
      case 'bearish':
        return 'trend-bearish';
      case 'neutral':
      case 'sideways':
        return 'trend-neutral';
      default:
        return 'trend-unknown';
    }
  };

  const getRsiSignal = (rsi: number): { text: string; color: string } => {
    if (rsi > 70) return { text: 'Overbought', color: 'signal-bearish' };
    if (rsi < 30) return { text: 'Oversold', color: 'signal-bullish' };
    return { text: 'Neutral', color: 'signal-neutral' };
  };

  return (
    <div className={`market-analysis-section ${className}`}>
      <div className="market-analysis-section__header">
        <h3 className="market-analysis-section__title">
          Market Analysis - {symbol}
        </h3>
        {analysis?.timestamp && (
          <div className="market-analysis-section__timestamp">
            Updated: {new Date(analysis.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
      
      {analysis && (
        <div className="market-analysis-section__content">
          {/* Overall Trend */}
          <div className="market-analysis-section__trend">
            <div className="trend-indicator">
              <div className="trend-indicator__icon">
                {getTrendIcon(analysis.trend)}
              </div>
              <div className="trend-indicator__info">
                <div className={`trend-indicator__label ${getTrendColor(analysis.trend)}`}>
                  {analysis.trend?.toUpperCase() || 'UNKNOWN'}
                </div>
                <div className="trend-indicator__strength">
                  Confidence: {(analysis.confidence * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>

          {/* Technical Indicators */}
          <div className="market-analysis-section__indicators">
            <h4 className="section-subtitle">Technical Indicators</h4>
            
            <div className="indicators-grid">
              {analysis.indicators?.map((indicator, index) => (
                <div key={index} className="indicator-item">
                  <div className="indicator-item__name">{indicator.name}</div>
                  <div className="indicator-item__value">
                    {typeof indicator.value === 'number' ? indicator.value.toFixed(4) : indicator.value}
                  </div>
                  {indicator.name === 'RSI' && typeof indicator.value === 'number' && (
                    <div className={`indicator-item__signal ${getRsiSignal(indicator.value).color}`}>
                      {getRsiSignal(indicator.value).text}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Support and Resistance (if available) */}
          {(analysis as any).analysis?.support && (analysis as any).analysis?.resistance && (
            <div className="market-analysis-section__levels">
              <h4 className="section-subtitle">Key Levels</h4>
              <div className="levels-grid">
                <div className="level-group">
                  <div className="level-group__title">Support Levels</div>
                  <div className="level-group__values">
                    {(analysis as any).analysis.support.map((level: number, index: number) => (
                      <span key={index} className="level-value level-value--support">
                        {level.toFixed(2)}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="level-group">
                  <div className="level-group__title">Resistance Levels</div>
                  <div className="level-group__values">
                    {(analysis as any).analysis.resistance.map((level: number, index: number) => (
                      <span key={index} className="level-value level-value--resistance">
                        {level.toFixed(2)}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Detected Patterns (if available) */}
          {(analysis as any).patterns && (analysis as any).patterns.length > 0 && (
            <div className="market-analysis-section__patterns">
              <h4 className="section-subtitle">Detected Patterns</h4>
              <div className="patterns-list">
                {(analysis as any).patterns.map((pattern: any, index: number) => (
                  <div key={index} className="pattern-item">
                    <div className="pattern-item__name">{pattern.name}</div>
                    <div className="pattern-item__confidence">
                      {(pattern.confidence * 100).toFixed(1)}%
                    </div>
                    {pattern.timeframe && (
                      <div className="pattern-item__timeframe">{pattern.timeframe}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Summary (if available) */}
          {(analysis as any).summary && (
            <div className="market-analysis-section__summary">
              <h4 className="section-subtitle">Analysis Summary</h4>
              <p className="summary-text">{(analysis as any).summary}</p>
            </div>
          )}

          {/* Signals (if available) */}
          {(analysis as any).signals && (analysis as any).signals.length > 0 && (
            <div className="market-analysis-section__signals">
              <h4 className="section-subtitle">Trading Signals</h4>
              <div className="signals-list">
                {(analysis as any).signals.map((signal: any, index: number) => (
                  <div key={index} className="signal-item">
                    <div className="signal-item__type">{signal.type}</div>
                    <div className="signal-item__strength">
                      Strength: {signal.strength.toFixed(2)}
                    </div>
                    <div className="signal-item__description">{signal.description}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};