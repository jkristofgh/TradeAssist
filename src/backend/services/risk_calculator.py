"""
Risk Calculator Service

Provides risk assessment, Value at Risk (VaR) calculations, and risk metrics
for the TradeAssist platform Phase 4 implementation.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
from scipy import stats
import math

from ..database.connection import get_db_session
from ..models.market_data import MarketData
from ..models.instruments import Instrument
from ..models.alert_rules import AlertRule
from sqlalchemy import select, and_
from .market_data_processor import market_data_processor, DataFrequency

logger = logging.getLogger(__name__)


class RiskMetricType(Enum):
    """Types of risk metrics."""
    VAR = "value_at_risk"
    CVAR = "conditional_var"
    VOLATILITY = "volatility"
    BETA = "beta"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    CORRELATION = "correlation"
    DOWNSIDE_DEVIATION = "downside_deviation"


class ConfidenceLevel(Enum):
    """Confidence levels for risk calculations."""
    NINETY_FIVE = 0.95
    NINETY_NINE = 0.99
    NINETY_NINE_NINE = 0.999


@dataclass
class VaRResult:
    """Value at Risk calculation result."""
    timestamp: datetime
    instrument_id: int
    var_amount: float
    confidence_level: float
    time_horizon_days: int
    method: str
    current_position: float
    portfolio_value: float
    volatility: float
    metadata: Dict[str, Any]


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics for an instrument or portfolio."""
    timestamp: datetime
    instrument_id: Optional[int]
    portfolio_id: Optional[str]
    
    # Risk measures
    var_95: float
    var_99: float
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    volatility_annual: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    
    # Market risk measures  
    beta: Optional[float]
    correlation_to_market: Optional[float]
    tracking_error: Optional[float]
    
    # Additional metrics
    skewness: float
    kurtosis: float
    downside_deviation: float
    calmar_ratio: float
    
    # Metadata
    data_period_days: int
    last_updated: datetime


@dataclass
class StressTestResult:
    """Stress test scenario result."""
    scenario_name: str
    timestamp: datetime
    instrument_id: int
    shock_magnitude: float
    original_value: float
    stressed_value: float
    loss_amount: float
    loss_percentage: float
    recovery_time_estimate_days: Optional[int]


@dataclass
class CorrelationMatrix:
    """Correlation matrix for multiple instruments."""
    timestamp: datetime
    instrument_ids: List[int]
    correlation_matrix: List[List[float]]
    eigenvalues: List[float]
    condition_number: float
    period_days: int


class RiskCalculator:
    """
    Advanced risk calculator for trading strategies and portfolios.
    
    Provides VaR calculations, stress testing, correlation analysis,
    and comprehensive risk metrics for informed trading decisions.
    """
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        self.trading_days_per_year = 252
        self.default_var_horizon = 1  # 1 day
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes cache
        
        # Benchmark data (would be loaded from external source in production)
        self.benchmark_returns: Optional[pd.Series] = None
    
    async def calculate_var(
        self,
        instrument_id: int,
        confidence_level: ConfidenceLevel = ConfidenceLevel.NINETY_FIVE,
        time_horizon_days: int = 1,
        position_size: float = 10000.0,
        method: str = "historical"
    ) -> Optional[VaRResult]:
        """
        Calculate Value at Risk for an instrument.
        
        Args:
            instrument_id: ID of the instrument.
            confidence_level: Confidence level for VaR calculation.
            time_horizon_days: Time horizon in days.
            position_size: Position size in dollars.
            method: VaR calculation method ('historical', 'parametric', 'monte_carlo').
            
        Returns:
            VaRResult: VaR calculation result or None.
        """
        try:
            # Get historical returns data
            returns = await self._get_returns_data(instrument_id, 252)  # 1 year of data
            if returns.empty or len(returns) < 30:
                logger.warning(f"Insufficient data for VaR calculation")
                return None
            
            # Calculate VaR based on method
            if method == "historical":
                var_amount = await self._calculate_historical_var(
                    returns, confidence_level.value, time_horizon_days
                )
            elif method == "parametric":
                var_amount = await self._calculate_parametric_var(
                    returns, confidence_level.value, time_horizon_days
                )
            elif method == "monte_carlo":
                var_amount = await self._calculate_monte_carlo_var(
                    returns, confidence_level.value, time_horizon_days
                )
            else:
                logger.warning(f"Unknown VaR method: {method}")
                return None
            
            # Scale VaR to position size
            var_dollar_amount = var_amount * position_size
            
            # Calculate current volatility
            volatility = returns.std() * np.sqrt(self.trading_days_per_year)
            
            return VaRResult(
                timestamp=datetime.utcnow(),
                instrument_id=instrument_id,
                var_amount=float(var_dollar_amount),
                confidence_level=confidence_level.value,
                time_horizon_days=time_horizon_days,
                method=method,
                current_position=position_size,
                portfolio_value=position_size,
                volatility=float(volatility),
                metadata={
                    'data_points': len(returns),
                    'return_period_start': returns.index[0].isoformat() if len(returns) > 0 else None,
                    'return_period_end': returns.index[-1].isoformat() if len(returns) > 0 else None,
                    'mean_return': float(returns.mean()),
                    'std_return': float(returns.std())
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return None
    
    async def calculate_comprehensive_risk_metrics(
        self,
        instrument_id: int,
        lookback_days: int = 252,
        benchmark_instrument_id: Optional[int] = None
    ) -> Optional[RiskMetrics]:
        """
        Calculate comprehensive risk metrics for an instrument.
        
        Args:
            instrument_id: ID of the instrument.
            lookback_days: Days of historical data to use.
            benchmark_instrument_id: ID of benchmark instrument for beta calculation.
            
        Returns:
            RiskMetrics: Comprehensive risk metrics or None.
        """
        try:
            # Get returns data
            returns = await self._get_returns_data(instrument_id, lookback_days)
            if returns.empty or len(returns) < 30:
                return None
            
            # Get benchmark returns if specified
            benchmark_returns = None
            if benchmark_instrument_id:
                benchmark_returns = await self._get_returns_data(
                    benchmark_instrument_id, lookback_days
                )
            
            # Calculate basic risk metrics
            annual_volatility = returns.std() * np.sqrt(self.trading_days_per_year)
            mean_return = returns.mean() * self.trading_days_per_year
            
            # VaR calculations
            var_95 = await self._calculate_historical_var(returns, 0.95, 1)
            var_99 = await self._calculate_historical_var(returns, 0.99, 1)
            cvar_95 = await self._calculate_conditional_var(returns, 0.95)
            
            # Drawdown analysis
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # Sharpe ratio
            excess_returns = returns - (self.risk_free_rate / self.trading_days_per_year)
            sharpe_ratio = (excess_returns.mean() * self.trading_days_per_year) / annual_volatility
            
            # Sortino ratio (downside deviation)
            downside_returns = returns[returns < 0]
            downside_deviation = downside_returns.std() * np.sqrt(self.trading_days_per_year)
            sortino_ratio = mean_return / downside_deviation if downside_deviation > 0 else 0
            
            # Higher moments
            skewness = returns.skew()
            kurtosis = returns.kurtosis()
            
            # Calmar ratio
            calmar_ratio = mean_return / abs(max_drawdown) if max_drawdown < 0 else 0
            
            # Beta and correlation (if benchmark available)
            beta = None
            correlation_to_market = None
            tracking_error = None
            
            if benchmark_returns is not None and not benchmark_returns.empty:
                # Align returns
                aligned_data = pd.concat([returns, benchmark_returns], axis=1, join='inner')
                if len(aligned_data) > 10:
                    asset_returns = aligned_data.iloc[:, 0]
                    bench_returns = aligned_data.iloc[:, 1]
                    
                    # Calculate beta
                    covariance = np.cov(asset_returns, bench_returns)[0, 1]
                    benchmark_variance = bench_returns.var()
                    beta = covariance / benchmark_variance if benchmark_variance > 0 else None
                    
                    # Correlation
                    correlation_to_market = asset_returns.corr(bench_returns)
                    
                    # Tracking error
                    tracking_error = (asset_returns - bench_returns).std() * np.sqrt(self.trading_days_per_year)
            
            return RiskMetrics(
                timestamp=datetime.utcnow(),
                instrument_id=instrument_id,
                portfolio_id=None,
                var_95=float(var_95 * 10000),  # Scale to $10,000 position
                var_99=float(var_99 * 10000),
                cvar_95=float(cvar_95 * 10000),
                volatility_annual=float(annual_volatility),
                max_drawdown=float(max_drawdown),
                sharpe_ratio=float(sharpe_ratio),
                sortino_ratio=float(sortino_ratio),
                beta=float(beta) if beta is not None else None,
                correlation_to_market=float(correlation_to_market) if correlation_to_market is not None else None,
                tracking_error=float(tracking_error) if tracking_error is not None else None,
                skewness=float(skewness),
                kurtosis=float(kurtosis),
                downside_deviation=float(downside_deviation),
                calmar_ratio=float(calmar_ratio),
                data_period_days=len(returns),
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive risk metrics: {e}")
            return None
    
    async def perform_stress_test(
        self,
        instrument_id: int,
        scenarios: Optional[List[Dict[str, Any]]] = None
    ) -> List[StressTestResult]:
        """
        Perform stress tests on an instrument.
        
        Args:
            instrument_id: ID of the instrument.
            scenarios: List of stress test scenarios.
            
        Returns:
            List[StressTestResult]: Stress test results.
        """
        try:
            if scenarios is None:
                scenarios = self._get_default_stress_scenarios()
            
            # Get current price
            current_price = await self._get_current_price(instrument_id)
            if current_price is None:
                return []
            
            # Get historical volatility for recovery estimates
            returns = await self._get_returns_data(instrument_id, 252)
            daily_volatility = returns.std() if not returns.empty else 0.02
            
            results = []
            
            for scenario in scenarios:
                shock_magnitude = scenario.get('shock_magnitude', 0.0)
                scenario_name = scenario.get('name', 'Unknown Scenario')
                
                # Calculate stressed price
                if scenario.get('type') == 'multiplicative':
                    stressed_price = current_price * (1 + shock_magnitude)
                else:  # additive
                    stressed_price = current_price + shock_magnitude
                
                loss_amount = stressed_price - current_price
                loss_percentage = loss_amount / current_price
                
                # Estimate recovery time (simplified)
                recovery_time = self._estimate_recovery_time(
                    abs(loss_percentage), daily_volatility
                ) if daily_volatility > 0 else None
                
                result = StressTestResult(
                    scenario_name=scenario_name,
                    timestamp=datetime.utcnow(),
                    instrument_id=instrument_id,
                    shock_magnitude=shock_magnitude,
                    original_value=current_price,
                    stressed_value=stressed_price,
                    loss_amount=loss_amount,
                    loss_percentage=loss_percentage,
                    recovery_time_estimate_days=recovery_time
                )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing stress test: {e}")
            return []
    
    async def calculate_correlation_matrix(
        self,
        instrument_ids: List[int],
        lookback_days: int = 252
    ) -> Optional[CorrelationMatrix]:
        """
        Calculate correlation matrix for multiple instruments.
        
        Args:
            instrument_ids: List of instrument IDs.
            lookback_days: Days of historical data to use.
            
        Returns:
            CorrelationMatrix: Correlation analysis or None.
        """
        try:
            if len(instrument_ids) < 2:
                return None
            
            # Get returns for all instruments
            returns_data = []
            valid_instrument_ids = []
            
            for instrument_id in instrument_ids:
                returns = await self._get_returns_data(instrument_id, lookback_days)
                if not returns.empty and len(returns) > 30:
                    returns_data.append(returns)
                    valid_instrument_ids.append(instrument_id)
            
            if len(returns_data) < 2:
                return None
            
            # Combine returns into DataFrame
            combined_returns = pd.concat(returns_data, axis=1, join='inner')
            combined_returns.columns = [f'instrument_{id}' for id in valid_instrument_ids]
            
            if len(combined_returns) < 30:
                return None
            
            # Calculate correlation matrix
            correlation_matrix = combined_returns.corr()
            
            # Calculate eigenvalues for risk analysis
            eigenvalues = np.linalg.eigvals(correlation_matrix.values)
            condition_number = np.max(eigenvalues) / np.min(eigenvalues)
            
            return CorrelationMatrix(
                timestamp=datetime.utcnow(),
                instrument_ids=valid_instrument_ids,
                correlation_matrix=correlation_matrix.values.tolist(),
                eigenvalues=eigenvalues.tolist(),
                condition_number=float(condition_number),
                period_days=len(combined_returns)
            )
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return None
    
    async def _get_returns_data(
        self,
        instrument_id: int,
        lookback_days: int
    ) -> pd.Series:
        """Get returns data for an instrument."""
        try:
            # Try to get data from market data processor first
            ohlcv_data = await market_data_processor.get_ohlcv_data(
                instrument_id=instrument_id,
                frequency=DataFrequency.DAILY,
                start_time=datetime.utcnow() - timedelta(days=lookback_days),
                limit=lookback_days
            )
            
            if ohlcv_data:
                prices = pd.Series(
                    [bar.close for bar in ohlcv_data],
                    index=[bar.timestamp for bar in ohlcv_data]
                )
                returns = prices.pct_change().dropna()
                return returns
            
            # Fall back to database query
            async with get_db_session() as session:
                cutoff_time = datetime.utcnow() - timedelta(days=lookback_days)
                
                result = await session.execute(
                    select(MarketData)
                    .where(
                        and_(
                            MarketData.instrument_id == instrument_id,
                            MarketData.timestamp >= cutoff_time
                        )
                    )
                    .order_by(MarketData.timestamp)
                )
                
                records = result.scalars().all()
                
                if not records:
                    return pd.Series(dtype=float)
                
                # Convert to price series
                prices = pd.Series(
                    [float(record.price) for record in records if record.price],
                    index=[record.timestamp for record in records if record.price]
                )
                
                if len(prices) < 2:
                    return pd.Series(dtype=float)
                
                # Calculate returns
                returns = prices.pct_change().dropna()
                return returns
                
        except Exception as e:
            logger.error(f"Error getting returns data: {e}")
            return pd.Series(dtype=float)
    
    async def _get_current_price(self, instrument_id: int) -> Optional[float]:
        """Get current price for an instrument."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(MarketData)
                    .where(MarketData.instrument_id == instrument_id)
                    .order_by(MarketData.timestamp.desc())
                    .limit(1)
                )
                
                record = result.scalar_one_or_none()
                return float(record.price) if record and record.price else None
                
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    async def _calculate_historical_var(
        self,
        returns: pd.Series,
        confidence_level: float,
        time_horizon_days: int
    ) -> float:
        """Calculate historical VaR."""
        if returns.empty:
            return 0.0
        
        # Scale returns for time horizon
        scaled_returns = returns * np.sqrt(time_horizon_days)
        
        # Find the percentile
        percentile = (1 - confidence_level) * 100
        var = np.percentile(scaled_returns, percentile)
        
        return abs(var)  # Return positive VaR
    
    async def _calculate_parametric_var(
        self,
        returns: pd.Series,
        confidence_level: float,
        time_horizon_days: int
    ) -> float:
        """Calculate parametric (normal distribution) VaR."""
        if returns.empty:
            return 0.0
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Scale for time horizon
        scaled_mean = mean_return * time_horizon_days
        scaled_std = std_return * np.sqrt(time_horizon_days)
        
        # Calculate z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)
        
        # Calculate VaR
        var = scaled_mean + z_score * scaled_std
        
        return abs(var)
    
    async def _calculate_monte_carlo_var(
        self,
        returns: pd.Series,
        confidence_level: float,
        time_horizon_days: int,
        simulations: int = 10000
    ) -> float:
        """Calculate Monte Carlo VaR."""
        if returns.empty:
            return 0.0
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Generate random returns
        np.random.seed(42)  # For reproducibility
        simulated_returns = np.random.normal(
            mean_return * time_horizon_days,
            std_return * np.sqrt(time_horizon_days),
            simulations
        )
        
        # Calculate VaR
        percentile = (1 - confidence_level) * 100
        var = np.percentile(simulated_returns, percentile)
        
        return abs(var)
    
    async def _calculate_conditional_var(
        self,
        returns: pd.Series,
        confidence_level: float
    ) -> float:
        """Calculate Conditional VaR (Expected Shortfall)."""
        if returns.empty:
            return 0.0
        
        percentile = (1 - confidence_level) * 100
        var_threshold = np.percentile(returns, percentile)
        
        # Calculate average of returns below VaR threshold
        tail_returns = returns[returns <= var_threshold]
        cvar = tail_returns.mean() if not tail_returns.empty else var_threshold
        
        return abs(cvar)
    
    def _get_default_stress_scenarios(self) -> List[Dict[str, Any]]:
        """Get default stress test scenarios."""
        return [
            {'name': 'Market Crash (-20%)', 'type': 'multiplicative', 'shock_magnitude': -0.20},
            {'name': 'Market Correction (-10%)', 'type': 'multiplicative', 'shock_magnitude': -0.10},
            {'name': 'Flash Crash (-5%)', 'type': 'multiplicative', 'shock_magnitude': -0.05},
            {'name': 'Volatility Spike (+50%)', 'type': 'volatility', 'shock_magnitude': 0.50},
            {'name': 'Interest Rate Shock', 'type': 'multiplicative', 'shock_magnitude': -0.15},
            {'name': 'Currency Crisis', 'type': 'multiplicative', 'shock_magnitude': -0.25}
        ]
    
    def _estimate_recovery_time(
        self,
        loss_magnitude: float,
        daily_volatility: float
    ) -> Optional[int]:
        """Estimate recovery time from a loss."""
        if daily_volatility <= 0:
            return None
        
        # Simple heuristic: recovery time is inversely related to volatility
        # Higher volatility means faster potential recovery but also more risk
        base_recovery_days = loss_magnitude / (daily_volatility * 2)  # Conservative estimate
        
        # Add some randomness and bounds
        recovery_days = max(1, min(365, int(base_recovery_days)))
        
        return recovery_days


# Global risk calculator instance
risk_calculator = RiskCalculator()