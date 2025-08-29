/**
 * Predictive Models Component
 * 
 * Displays ML-based price predictions, trend classifications, and anomaly detection
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface PredictiveModelsProps {
  instrumentId: number;
  currentPrice: number;
}

interface PredictionResult {
  model_type: string;
  timestamp: string;
  predicted_value: number;
  confidence_score: number;
  prediction_horizon: string;
  feature_importance: Record<string, number>;
  metadata: Record<string, any>;
}

interface TrendClassification {
  trend: string;
  confidence: number;
  trend_slope: number;
  volatility: number;
  momentum: number;
}

const PredictiveModels: React.FC<PredictiveModelsProps> = ({ instrumentId, currentPrice }) => {
  const [predictions, setPredictions] = useState<{[key: string]: PredictionResult}>({});
  const [trendClassification, setTrendClassification] = useState<TrendClassification | null>(null);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchPredictions = async () => {
    setLoading(true);
    try {
      // Fetch LSTM prediction
      const lstmResponse = await axios.post('/api/v1/analytics/predict-price', {
        instrument_id: instrumentId,
        model_type: 'lstm_price_predictor',
        horizon: 'short_term'
      });
      
      // Fetch Random Forest prediction
      const rfResponse = await axios.post('/api/v1/analytics/predict-price', {
        instrument_id: instrumentId,
        model_type: 'random_forest_predictor',
        horizon: 'short_term'
      });

      setPredictions({
        lstm: lstmResponse.data,
        random_forest: rfResponse.data
      });

      // Fetch trend classification
      const trendResponse = await axios.get(`/api/v1/analytics/trend-classification/${instrumentId}`);
      setTrendClassification(trendResponse.data);

      // Fetch anomalies
      const anomalyResponse = await axios.get(`/api/v1/analytics/anomaly-detection/${instrumentId}`);
      setAnomalies(anomalyResponse.data.anomalies || []);

    } catch (error) {
      console.error('Failed to fetch predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, [instrumentId]);

  const getPredictionColor = (predicted: number, current: number) => {
    if (predicted > current) return '#4caf50';
    if (predicted < current) return '#f44336';
    return '#ff9800';
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'bullish': return '#4caf50';
      case 'bearish': return '#f44336';
      default: return '#ff9800';
    }
  };

  return (
    <div className="predictive-models">
      <div className="models-header">
        <h2>ML Predictions & Analysis</h2>
        <button onClick={fetchPredictions} disabled={loading} className="refresh-btn">
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      <div className="predictions-grid">
        {Object.entries(predictions).map(([model, prediction]) => (
          <div key={model} className="prediction-card">
            <h3>{model.replace('_', ' ').toUpperCase()}</h3>
            <div className="prediction-value" style={{ color: getPredictionColor(prediction.predicted_value, currentPrice) }}>
              ${prediction.predicted_value.toFixed(4)}
            </div>
            <div className="prediction-change">
              {((prediction.predicted_value - currentPrice) / currentPrice * 100).toFixed(2)}%
            </div>
            <div className="confidence-meter">
              <div className="confidence-bar">
                <div 
                  className="confidence-fill" 
                  style={{ width: `${prediction.confidence_score * 100}%` }}
                />
              </div>
              <span>{(prediction.confidence_score * 100).toFixed(0)}% confidence</span>
            </div>
          </div>
        ))}
      </div>

      {trendClassification && (
        <div className="trend-classification">
          <h3>Trend Classification</h3>
          <div className="trend-result">
            <div className="trend-badge" style={{ backgroundColor: getTrendColor(trendClassification.trend) }}>
              {trendClassification.trend.toUpperCase()}
            </div>
            <div className="trend-metrics">
              <div>Confidence: {(trendClassification.confidence * 100).toFixed(0)}%</div>
              <div>Momentum: {(trendClassification.momentum * 100).toFixed(2)}%</div>
            </div>
          </div>
        </div>
      )}

      <div className="anomaly-detection">
        <h3>Market Anomalies</h3>
        {anomalies.length > 0 ? (
          <div className="anomalies-list">
            {anomalies.slice(0, 5).map((anomaly, index) => (
              <div key={index} className={`anomaly-item ${anomaly.severity}`}>
                <div className="anomaly-time">{new Date(anomaly.timestamp).toLocaleTimeString()}</div>
                <div className="anomaly-severity">{anomaly.severity.toUpperCase()}</div>
                <div className="anomaly-score">Score: {anomaly.anomaly_score.toFixed(3)}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-anomalies">No significant anomalies detected</div>
        )}
      </div>
    </div>
  );
};

export default PredictiveModels;