/**
 * Price Prediction Section Component
 * 
 * Displays ML-based price predictions with confidence intervals
 * and prediction charts.
 */

import React from 'react';
import { usePricePrediction } from '../../hooks/useAnalytics';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import './PricePredictionSection.css';

interface PricePredictionSectionProps {
  instrumentId: number;
  symbol: string;
  className?: string;
}

export const PricePredictionSection: React.FC<PricePredictionSectionProps> = ({
  instrumentId,
  symbol,
  className = ''
}) => {
  const { data: prediction, isLoading, error, refetch } = usePricePrediction(instrumentId, 24, {
    modelType: 'ensemble',
    confidenceLevel: 0.95
  });

  if (error) {
    return (
      <div className={`price-prediction-section ${className}`}>
        <div className="price-prediction-section__header">
          <h3 className="price-prediction-section__title">Price Predictions</h3>
        </div>
        <ErrorAlert 
          message="Failed to load price predictions" 
          error={error}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`price-prediction-section ${className}`}>
        <div className="price-prediction-section__header">
          <h3 className="price-prediction-section__title">Price Predictions</h3>
        </div>
        <div className="price-prediction-section__loading">
          <LoadingSpinner size="medium" />
          <p>Generating ML predictions...</p>
        </div>
      </div>
    );
  }

  const formatPrice = (price: number): string => {
    return price.toFixed(2);
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };

  return (
    <div className={`price-prediction-section ${className}`}>
      <div className="price-prediction-section__header">
        <h3 className="price-prediction-section__title">
          Price Predictions - {symbol}
        </h3>
        {prediction?.timestamp && (
          <div className="price-prediction-section__timestamp">
            Generated: {new Date(prediction.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
      
      {prediction && (
        <div className="price-prediction-section__content">
          {/* Main Prediction */}
          <div className="prediction-main">
            <div className="prediction-main__price">
              <div className="prediction-main__label">Predicted Price (24h)</div>
              <div className="prediction-main__value">${formatPrice(prediction.predictedPrice)}</div>
              <div className="prediction-main__confidence">
                Confidence: {formatPercentage(prediction.confidence)}
              </div>
            </div>
            
            {prediction.priceRange && (
              <div className="prediction-range">
                <div className="prediction-range__item">
                  <div className="prediction-range__label">Low</div>
                  <div className="prediction-range__value prediction-range__value--low">
                    ${formatPrice(prediction.priceRange.low)}
                  </div>
                </div>
                <div className="prediction-range__item">
                  <div className="prediction-range__label">High</div>
                  <div className="prediction-range__value prediction-range__value--high">
                    ${formatPrice(prediction.priceRange.high)}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Model Information */}
          <div className="model-info">
            <h4 className="section-subtitle">Model Information</h4>
            <div className="model-info__grid">
              <div className="model-info__item">
                <div className="model-info__label">Model Type</div>
                <div className="model-info__value">{prediction.modelUsed}</div>
              </div>
              <div className="model-info__item">
                <div className="model-info__label">Horizon</div>
                <div className="model-info__value">{prediction.predictionHorizon}h</div>
              </div>
            </div>
          </div>

          {/* Contributing Factors */}
          {prediction.factors && prediction.factors.length > 0 && (
            <div className="prediction-factors">
              <h4 className="section-subtitle">Contributing Factors</h4>
              <div className="factors-list">
                {prediction.factors.map((factor, index) => (
                  <div key={index} className="factor-item">
                    <div className="factor-item__header">
                      <div className="factor-item__name">{factor.name}</div>
                      <div className={`factor-item__impact ${
                        factor.impact > 0 ? 'factor-item__impact--positive' : 
                        factor.impact < 0 ? 'factor-item__impact--negative' : 
                        'factor-item__impact--neutral'
                      }`}>
                        {factor.impact > 0 ? '+' : ''}{formatPercentage(factor.impact)}
                      </div>
                    </div>
                    <div className="factor-item__description">{factor.description}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Disclaimer */}
          <div className="prediction-disclaimer">
            <div className="prediction-disclaimer__icon">⚠️</div>
            <div className="prediction-disclaimer__text">
              Predictions are based on historical data and machine learning models. 
              Past performance does not guarantee future results. Use for informational purposes only.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};