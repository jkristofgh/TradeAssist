/**
 * Technical Indicators Section Component
 * 
 * Displays real-time technical indicators including RSI, MACD, Bollinger Bands,
 * and other momentum and trend indicators with visual progress bars and signals.
 */

import React from 'react';
import { useRealTimeIndicators } from '../../hooks/useAnalytics';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import './TechnicalIndicatorsSection.css';

interface TechnicalIndicatorsSectionProps {
  instrumentId: number;
  symbol: string;
  className?: string;
}

export const TechnicalIndicatorsSection: React.FC<TechnicalIndicatorsSectionProps> = ({
  instrumentId,
  symbol,
  className = ''
}) => {
  const { data: indicators, isLoading, error, refetch } = useRealTimeIndicators(instrumentId, {
    timeframe: 'minute',
    lookbackPeriod: 100
  });

  if (error) {
    return (
      <div className={`technical-indicators-section ${className}`}>
        <div className="technical-indicators-section__header">
          <h3 className="technical-indicators-section__title">Technical Indicators</h3>
        </div>
        <ErrorAlert 
          message="Failed to load technical indicators" 
          error={error}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`technical-indicators-section ${className}`}>
        <div className="technical-indicators-section__header">
          <h3 className="technical-indicators-section__title">Technical Indicators</h3>
        </div>
        <div className="technical-indicators-section__loading">
          <LoadingSpinner size="medium" />
          <p>Loading real-time indicators...</p>
        </div>
      </div>
    );
  }

  const getRsiStatus = (rsi: number): { label: string; color: string } => {
    if (rsi > 70) return { label: 'Overbought', color: 'rsi-overbought' };
    if (rsi < 30) return { label: 'Oversold', color: 'rsi-oversold' };
    return { label: 'Neutral', color: 'rsi-neutral' };
  };

  const getMacdSignal = (macd: any): { label: string; color: string } => {
    if (!macd || typeof macd.macd !== 'number' || typeof macd.signal !== 'number') {
      return { label: 'No Signal', color: 'macd-neutral' };
    }
    
    if (macd.macd > macd.signal) {
      return { label: 'Bullish', color: 'macd-bullish' };
    } else if (macd.macd < macd.signal) {
      return { label: 'Bearish', color: 'macd-bearish' };
    }
    return { label: 'Neutral', color: 'macd-neutral' };
  };

  const formatIndicatorValue = (value: any): string => {
    if (typeof value === 'number') {
      return value.toFixed(4);
    }
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value);
    }
    return String(value || 'N/A');
  };

  return (
    <div className={`technical-indicators-section ${className}`}>
      <div className="technical-indicators-section__header">
        <h3 className="technical-indicators-section__title">
          Technical Indicators - {symbol}
        </h3>
        {indicators?.timestamp && (
          <div className="technical-indicators-section__timestamp">
            Updated: {new Date(indicators.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
      
      {indicators && (
        <div className="technical-indicators-section__content">
          {/* RSI Indicator */}
          {typeof indicators.indicators.rsi === 'number' && (
            <div className="indicator-widget">
              <div className="indicator-widget__header">
                <h4 className="indicator-widget__title">RSI (14)</h4>
                <div className="indicator-widget__value">
                  {indicators.indicators.rsi.toFixed(2)}
                </div>
              </div>
              <div className="indicator-widget__body">
                <div className="rsi-gauge">
                  <div className="rsi-gauge__track">
                    <div 
                      className="rsi-gauge__fill" 
                      style={{ width: `${indicators.indicators.rsi}%` }}
                    />
                    <div className="rsi-gauge__markers">
                      <div className="rsi-gauge__marker" style={{ left: '30%' }}>30</div>
                      <div className="rsi-gauge__marker" style={{ left: '50%' }}>50</div>
                      <div className="rsi-gauge__marker" style={{ left: '70%' }}>70</div>
                    </div>
                  </div>
                </div>
                <div className={`indicator-status ${getRsiStatus(indicators.indicators.rsi).color}`}>
                  {getRsiStatus(indicators.indicators.rsi).label}
                </div>
              </div>
            </div>
          )}

          {/* MACD Indicator */}
          {indicators.indicators.macd && (
            <div className="indicator-widget">
              <div className="indicator-widget__header">
                <h4 className="indicator-widget__title">MACD</h4>
                <div className={`indicator-status ${getMacdSignal(indicators.indicators.macd).color}`}>
                  {getMacdSignal(indicators.indicators.macd).label}
                </div>
              </div>
              <div className="indicator-widget__body">
                <div className="macd-values">
                  <div className="macd-value">
                    <span className="macd-value__label">MACD:</span>
                    <span className="macd-value__number">
                      {formatIndicatorValue(indicators.indicators.macd.macd)}
                    </span>
                  </div>
                  <div className="macd-value">
                    <span className="macd-value__label">Signal:</span>
                    <span className="macd-value__number">
                      {formatIndicatorValue(indicators.indicators.macd.signal)}
                    </span>
                  </div>
                  <div className="macd-value">
                    <span className="macd-value__label">Histogram:</span>
                    <span className="macd-value__number">
                      {formatIndicatorValue(indicators.indicators.macd.histogram)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Bollinger Bands */}
          {indicators.indicators.bollingerBands && (
            <div className="indicator-widget">
              <div className="indicator-widget__header">
                <h4 className="indicator-widget__title">Bollinger Bands</h4>
              </div>
              <div className="indicator-widget__body">
                <div className="bb-values">
                  <div className="bb-band bb-band--upper">
                    <span className="bb-band__label">Upper:</span>
                    <span className="bb-band__value">
                      {formatIndicatorValue(indicators.indicators.bollingerBands.upper)}
                    </span>
                  </div>
                  <div className="bb-band bb-band--middle">
                    <span className="bb-band__label">Middle:</span>
                    <span className="bb-band__value">
                      {formatIndicatorValue(indicators.indicators.bollingerBands.middle)}
                    </span>
                  </div>
                  <div className="bb-band bb-band--lower">
                    <span className="bb-band__label">Lower:</span>
                    <span className="bb-band__value">
                      {formatIndicatorValue(indicators.indicators.bollingerBands.lower)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Moving Averages */}
          {indicators.indicators.movingAverages && (
            <div className="indicator-widget">
              <div className="indicator-widget__header">
                <h4 className="indicator-widget__title">Moving Averages</h4>
              </div>
              <div className="indicator-widget__body">
                <div className="ma-grid">
                  {indicators.indicators.movingAverages.sma20 && (
                    <div className="ma-item">
                      <span className="ma-item__label">SMA 20:</span>
                      <span className="ma-item__value">
                        {formatIndicatorValue(indicators.indicators.movingAverages.sma20)}
                      </span>
                    </div>
                  )}
                  {indicators.indicators.movingAverages.sma50 && (
                    <div className="ma-item">
                      <span className="ma-item__label">SMA 50:</span>
                      <span className="ma-item__value">
                        {formatIndicatorValue(indicators.indicators.movingAverages.sma50)}
                      </span>
                    </div>
                  )}
                  {indicators.indicators.movingAverages.ema12 && (
                    <div className="ma-item">
                      <span className="ma-item__label">EMA 12:</span>
                      <span className="ma-item__value">
                        {formatIndicatorValue(indicators.indicators.movingAverages.ema12)}
                      </span>
                    </div>
                  )}
                  {indicators.indicators.movingAverages.ema26 && (
                    <div className="ma-item">
                      <span className="ma-item__label">EMA 26:</span>
                      <span className="ma-item__value">
                        {formatIndicatorValue(indicators.indicators.movingAverages.ema26)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Stochastic Oscillator */}
          {indicators.indicators.stochastic && (
            <div className="indicator-widget">
              <div className="indicator-widget__header">
                <h4 className="indicator-widget__title">Stochastic</h4>
              </div>
              <div className="indicator-widget__body">
                <div className="stoch-values">
                  <div className="stoch-value">
                    <span className="stoch-value__label">%K:</span>
                    <span className="stoch-value__number">
                      {formatIndicatorValue(indicators.indicators.stochastic.k)}
                    </span>
                  </div>
                  <div className="stoch-value">
                    <span className="stoch-value__label">%D:</span>
                    <span className="stoch-value__number">
                      {formatIndicatorValue(indicators.indicators.stochastic.d)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ATR */}
          {typeof indicators.indicators.atr === 'number' && (
            <div className="indicator-widget">
              <div className="indicator-widget__header">
                <h4 className="indicator-widget__title">ATR (14)</h4>
                <div className="indicator-widget__value">
                  {indicators.indicators.atr.toFixed(4)}
                </div>
              </div>
            </div>
          )}

          {/* Next Update Info */}
          {(indicators as any).nextUpdate && (
            <div className="technical-indicators-section__next-update">
              Next update: {new Date((indicators as any).nextUpdate).toLocaleTimeString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
};