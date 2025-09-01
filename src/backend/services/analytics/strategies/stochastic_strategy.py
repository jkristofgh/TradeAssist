"""
Stochastic Oscillator calculation strategy.

This strategy implements the Stochastic Oscillator technical indicator calculation using the same
mathematical approach as the original god method to ensure backward compatibility.
"""

import pandas as pd
import structlog
from typing import Dict, Any, Tuple
from datetime import datetime

from .base import IndicatorStrategy
from ...analytics_engine import IndicatorResult, TechnicalIndicator

logger = structlog.get_logger()


class StochasticStrategy(IndicatorStrategy):
    """
    Stochastic Oscillator calculation strategy.
    
    Current Implementation Analysis:
    - Existing calculation in god method lines 353-374 (22 lines)
    - Two components: %K and %D
    - Default parameters: k_period=14, d_period=3
    - Overbought: 80, Oversold: 20
    """
    
    async def calculate(self, market_data: pd.DataFrame,
                       instrument_id: int, **params) -> IndicatorResult:
        """
        Stochastic calculation requirements:
        - Support k_period and d_period parameters
        - Calculate %K: ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        - Calculate %D: SMA of %K over d_period
        - Return both %K and %D values
        - Include overbought/oversold levels
        """
        try:
            # Validate market data
            self._validate_market_data(market_data)
            
            # Get parameters
            k_period = params.get('k_period', 14)
            d_period = params.get('d_period', 3)
            
            # Additional validation for Stochastic-specific requirements
            min_data_points = k_period + d_period + 1
            if len(market_data) < min_data_points:
                raise ValueError(f"Insufficient data for Stochastic calculation: need {min_data_points}, got {len(market_data)}")
            
            # Calculate Stochastic using the same logic as original method
            k_percent, d_percent = self._calculate_stochastic(
                market_data['high'], market_data['low'], market_data['close'],
                k_period, d_period
            )
            
            # Get the latest values
            current_k = self._safe_iloc(k_percent, -1, 50.0)
            current_d = self._safe_iloc(d_percent, -1, 50.0)
            
            # Build result with same structure as original
            return IndicatorResult(
                indicator_type=TechnicalIndicator.STOCHASTIC,
                timestamp=self._calculate_timestamp(),
                instrument_id=instrument_id,
                values={
                    'k_percent': float(current_k),
                    'd_percent': float(current_d)
                },
                metadata={
                    'k_period': k_period,
                    'd_period': d_period
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error calculating Stochastic",
                instrument_id=instrument_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Default Stochastic parameters matching original implementation."""
        return {
            'k_period': 14,
            'd_period': 3
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate Stochastic parameters."""
        k_period = params.get('k_period')
        d_period = params.get('d_period')
        
        # Check both are integers
        if not isinstance(k_period, int) or not isinstance(d_period, int):
            return False
        
        # Check reasonable ranges
        if not (1 <= k_period <= 50):
            return False
        if not (1 <= d_period <= 20):
            return False
        
        return True
    
    def get_minimum_data_points(self) -> int:
        """Stochastic needs at least k_period + d_period + 1 data points."""
        return 18  # Default: 14 + 3 + 1
    
    def _calculate_stochastic(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator using identical logic to original method.
        
        This method is copied exactly from AnalyticsEngine._calculate_stochastic to ensure
        mathematical compatibility and identical results.
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = ((close - lowest_low) / (highest_high - lowest_low)) * 100
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent, d_percent