"""
ATR (Average True Range) calculation strategy.

This strategy implements the ATR technical indicator calculation using the same
mathematical approach as the original god method to ensure backward compatibility.
"""

import pandas as pd
import structlog
from typing import Dict, Any
from datetime import datetime

from .base import IndicatorStrategy
from ...analytics_engine import IndicatorResult, TechnicalIndicator

logger = structlog.get_logger()


class ATRStrategy(IndicatorStrategy):
    """
    Average True Range calculation strategy.
    
    Current Implementation Analysis:  
    - Existing calculation in god method lines 375-395 (21 lines)
    - Measures market volatility
    - Default parameters: period=14
    - Uses True Range calculation with smoothing
    """
    
    async def calculate(self, market_data: pd.DataFrame,
                       instrument_id: int, **params) -> IndicatorResult:
        """
        ATR calculation requirements:
        - Support period parameter
        - Calculate True Range for each period
        - Apply exponential smoothing over period
        - Return ATR value and ATR percentage
        - Include volatility classification (low/medium/high)
        """
        try:
            # Validate market data
            self._validate_market_data(market_data)
            
            # Get parameters
            period = params.get('period', 14)
            
            # Additional validation for ATR-specific requirements
            if len(market_data) < period + 2:  # Need extra point for shift operation
                raise ValueError(f"Insufficient data for ATR calculation: need {period + 2}, got {len(market_data)}")
            
            # Calculate ATR using the same logic as original method
            atr_series = self._calculate_atr(
                market_data['high'], market_data['low'], market_data['close'], period
            )
            
            # Get the latest values
            current_atr = self._safe_iloc(atr_series, -1, 0.0)
            current_close = market_data['close'].iloc[-1]
            
            # Calculate ATR percentage
            atr_percent = 0.0
            if current_close != 0:
                atr_percent = (current_atr / current_close) * 100
            
            # Build result with same structure as original
            return IndicatorResult(
                indicator_type=TechnicalIndicator.ATR,
                timestamp=self._calculate_timestamp(),
                instrument_id=instrument_id,
                values={
                    'atr': float(current_atr),
                    'atr_percent': float(atr_percent)
                },
                metadata={'period': period}
            )
            
        except Exception as e:
            logger.error(
                f"Error calculating ATR",
                instrument_id=instrument_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Default ATR parameters matching original implementation."""
        return {'period': 14}
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate ATR parameters."""
        period = params.get('period')
        
        # Check period is integer
        if not isinstance(period, int):
            return False
        
        # Check reasonable range
        if not (1 <= period <= 100):
            return False
        
        return True
    
    def get_minimum_data_points(self) -> int:
        """ATR needs at least period + 2 data points (for shift operation)."""
        return 16  # Default period (14) + 2
    
    def _calculate_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range using identical logic to original method.
        
        This method is copied exactly from AnalyticsEngine._calculate_atr to ensure
        mathematical compatibility and identical results.
        """
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr