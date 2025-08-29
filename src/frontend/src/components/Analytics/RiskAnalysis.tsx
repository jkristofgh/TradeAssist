/**
 * Risk Analysis Component
 * 
 * Displays VaR calculations, risk metrics, and stress testing results
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface RiskAnalysisProps {
  instrumentId: number;
  currentPrice: number;
  volatilityMetrics: {
    volatility_annualized: number;
    atr_percent: number;
  };
}

const RiskAnalysis: React.FC<RiskAnalysisProps> = ({ 
  instrumentId, 
  currentPrice, 
  volatilityMetrics 
}) => {
  const [varData, setVarData] = useState<any>(null);
  const [riskMetrics, setRiskMetrics] = useState<any>(null);
  const [stressTestResults, setStressTestResults] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchRiskData = async () => {
    setLoading(true);
    try {
      // Fetch VaR
      const varResponse = await axios.post('/api/v1/analytics/calculate-var', {
        instrument_id: instrumentId,
        confidence_level: 0.95,
        time_horizon_days: 1,
        position_size: 10000,
        method: 'historical'
      });
      setVarData(varResponse.data);

      // Fetch comprehensive risk metrics
      const riskResponse = await axios.get(`/api/v1/analytics/risk-metrics/${instrumentId}`);
      setRiskMetrics(riskResponse.data);

      // Fetch stress test results
      const stressResponse = await axios.post('/api/v1/analytics/stress-test', {
        instrument_id: instrumentId
      });
      setStressTestResults(stressResponse.data.stress_test_results || []);

    } catch (error) {
      console.error('Failed to fetch risk data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskData();
  }, [instrumentId]);

  const getRiskLevel = (value: number, thresholds: number[]) => {
    if (value < thresholds[0]) return { level: 'Low', color: '#4caf50' };
    if (value < thresholds[1]) return { level: 'Medium', color: '#ff9800' };
    return { level: 'High', color: '#f44336' };
  };

  return (
    <div className="risk-analysis">
      <div className="risk-header">
        <h2>Risk Analysis</h2>
        <button onClick={fetchRiskData} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {varData && (
        <div className="var-section">
          <h3>Value at Risk (VaR)</h3>
          <div className="var-card">
            <div className="var-amount">${varData.var_amount.toFixed(2)}</div>
            <div className="var-details">
              <div>95% Confidence, 1-day horizon</div>
              <div>Position: ${varData.current_position.toLocaleString()}</div>
              <div>Method: {varData.method}</div>
            </div>
          </div>
        </div>
      )}

      {riskMetrics && (
        <div className="risk-metrics-grid">
          <div className="metric-card">
            <h4>Sharpe Ratio</h4>
            <div className="metric-value">{riskMetrics.risk_metrics.sharpe_ratio.toFixed(2)}</div>
          </div>
          <div className="metric-card">
            <h4>Max Drawdown</h4>
            <div className="metric-value">{(riskMetrics.risk_metrics.max_drawdown * 100).toFixed(1)}%</div>
          </div>
          <div className="metric-card">
            <h4>Volatility</h4>
            <div className="metric-value">{(riskMetrics.risk_metrics.volatility_annual * 100).toFixed(1)}%</div>
          </div>
        </div>
      )}

      <div className="stress-test-section">
        <h3>Stress Test Results</h3>
        <div className="stress-test-grid">
          {stressTestResults.map((result, index) => (
            <div key={index} className="stress-test-card">
              <h4>{result.scenario_name}</h4>
              <div className="stress-loss" style={{ color: result.loss_percentage < 0 ? '#f44336' : '#4caf50' }}>
                {(result.loss_percentage * 100).toFixed(1)}%
              </div>
              <div className="stress-amount">${result.loss_amount.toFixed(2)}</div>
              {result.recovery_time_estimate_days && (
                <div className="recovery-time">
                  Est. Recovery: {result.recovery_time_estimate_days} days
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RiskAnalysis;