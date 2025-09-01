"""
MACD (Moving Average Convergence Divergence) calculation strategy.

This strategy implements the MACD technical indicator calculation using the same
mathematical approach as the original god method to ensure backward compatibility.
"""

import pandas as pd
import structlog
from typing import Dict, Any, Tuple
from datetime import datetime

from .base import IndicatorStrategy
from ...analytics_engine import IndicatorResult, TechnicalIndicator

logger = structlog.get_logger()


class MACDStrategy(IndicatorStrategy):
    """
    MACD (Moving Average Convergence Divergence) calculation strategy.
    
    Current Implementation Analysis:
    - Existing calculation in god method lines 302-325 (24 lines)
    - Three components: MACD line, Signal line, Histogram
    - Default parameters: fast_period=12, slow_period=26, signal_period=9
    - Uses exponential moving averages
    """
    
    async def calculate(self, market_data: pd.DataFrame,
                       instrument_id: int, **params) -> IndicatorResult:
        """
        MACD calculation requirements:
        - Support fast_period, slow_period, signal_period parameters
        - Calculate MACD line (fast EMA - slow EMA)
        - Calculate Signal line (EMA of MACD line)
        - Calculate Histogram (MACD line - Signal line)
        - Return all three values in result
        """
        try:
            # Validate market data
            self._validate_market_data(market_data)
            
            # Get parameters
            fast_period = params.get('fast_period', 12)
            slow_period = params.get('slow_period', 26)
            signal_period = params.get('signal_period', 9)
            
            # Additional validation for MACD-specific requirements
            min_data_points = max(slow_period, signal_period) + 10  # Extra buffer for EMA calculation
            if len(market_data) < min_data_points:
                raise ValueError(f"Insufficient data for MACD calculation: need {min_data_points}, got {len(market_data)}")
            
            # Calculate MACD using the same logic as original method
            macd_line, signal_line, histogram = self._calculate_macd(
                market_data['close'], fast_period, slow_period, signal_period
            )
            
            # Get the latest values
            current_macd = self._safe_iloc(macd_line, -1, 0.0)
            current_signal = self._safe_iloc(signal_line, -1, 0.0)
            current_histogram = self._safe_iloc(histogram, -1, 0.0)
            
            # Build result with same structure as original
            return IndicatorResult(
                indicator_type=TechnicalIndicator.MACD,
                timestamp=self._calculate_timestamp(),
                instrument_id=instrument_id,
                values={
                    'macd': float(current_macd),
                    'signal': float(current_signal),
                    'histogram': float(current_histogram)
                },
                metadata={
                    'fast': fast_period,
                    'slow': slow_period,
                    'signal': signal_period
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error calculating MACD",
                instrument_id=instrument_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Default MACD parameters matching original implementation."""
        return {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate MACD parameters."""
        fast_period = params.get('fast_period')
        slow_period = params.get('slow_period')
        signal_period = params.get('signal_period')
        
        # Check all are integers
        if not all(isinstance(p, int) for p in [fast_period, slow_period, signal_period]):
            return False
        
        # Check reasonable ranges
        if not (1 <= fast_period <= 50):
            return False
        if not (5 <= slow_period <= 100):
            return False
        if not (1 <= signal_period <= 50):
            return False
        
        # Fast period should be less than slow period
        if fast_period >= slow_period:
            return False
        
        return True
    
    def get_minimum_data_points(self) -> int:
        """MACD needs at least slow_period + signal_period + buffer."""
        return 45  # Conservative estimate: 26 + 9 + 10 buffer
    
    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD using identical logic to original method.
        
        This method is copied exactly from AnalyticsEngine._calculate_macd to ensure
        mathematical compatibility and identical results.
        """
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram