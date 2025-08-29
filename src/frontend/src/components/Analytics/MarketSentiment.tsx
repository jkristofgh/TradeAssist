/**
 * Market Sentiment Component
 * 
 * Displays market sentiment analysis and pattern signals
 */

import React from 'react';

interface MarketSentimentProps {
  instrumentId: number;
  patternSignals: Array<{
    pattern: string;
    signal: string;
    confidence: number;
    description: string;
  }>;
}

const MarketSentiment: React.FC<MarketSentimentProps> = ({ 
  instrumentId, 
  patternSignals 
}) => {
  const getSentimentScore = () => {
    if (patternSignals.length === 0) return 0;
    
    const bullishSignals = patternSignals.filter(p => p.signal === 'bullish');
    const bearishSignals = patternSignals.filter(p => p.signal === 'bearish');
    
    if (bullishSignals.length > bearishSignals.length) return 0.6;
    if (bearishSignals.length > bullishSignals.length) return -0.6;
    return 0;
  };

  const sentimentScore = getSentimentScore();
  const getSentimentLabel = (score: number) => {
    if (score > 0.3) return 'Bullish';
    if (score < -0.3) return 'Bearish';
    return 'Neutral';
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.3) return '#4caf50';
    if (score < -0.3) return '#f44336';
    return '#ff9800';
  };

  return (
    <div className="market-sentiment">
      <div className="sentiment-overview">
        <h2>Market Sentiment</h2>
        <div className="sentiment-gauge">
          <div className="gauge-container">
            <div className="gauge-track">
              <div 
                className="gauge-needle" 
                style={{ 
                  left: `${((sentimentScore + 1) / 2) * 100}%`,
                  backgroundColor: getSentimentColor(sentimentScore)
                }}
              />
            </div>
            <div className="gauge-labels">
              <span>Bearish</span>
              <span>Neutral</span>
              <span>Bullish</span>
            </div>
          </div>
          <div className="sentiment-label" style={{ color: getSentimentColor(sentimentScore) }}>
            {getSentimentLabel(sentimentScore)}
          </div>
        </div>
      </div>

      <div className="pattern-signals-section">
        <h3>Pattern Signals</h3>
        {patternSignals.length > 0 ? (
          <div className="signals-grid">
            {patternSignals.map((signal, index) => (
              <div key={index} className={`signal-card ${signal.signal}`}>
                <div className="signal-pattern">{signal.pattern.replace(/_/g, ' ')}</div>
                <div className={`signal-type ${signal.signal}`}>{signal.signal.toUpperCase()}</div>
                <div className="signal-confidence">{(signal.confidence * 100).toFixed(0)}%</div>
                <div className="signal-description">{signal.description}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-signals">No significant pattern signals detected</div>
        )}
      </div>
    </div>
  );
};

export default MarketSentiment;