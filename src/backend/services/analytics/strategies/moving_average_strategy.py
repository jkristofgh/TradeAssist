"""
Moving Average calculation strategy (supports SMA and EMA).

This strategy implements moving average calculations using the same
mathematical approach as the original god method to ensure backward compatibility.
"""

import pandas as pd
import structlog
from typing import Dict, Any, List, Union
from datetime import datetime

from .base import IndicatorStrategy
from ...analytics_engine import IndicatorResult, TechnicalIndicator

logger = structlog.get_logger()


class MovingAverageStrategy(IndicatorStrategy):
    """
    Moving Average calculation strategy (supports SMA and EMA).
    
    Current Implementation Analysis:
    - Existing calculation in god method lines 343-352 (10 lines)
    - Supports both Simple MA and Exponential MA
    - Default parameters: period=20, ma_type='sma'
    - Used as component in other indicators
    """
    
    async def calculate(self, market_data: pd.DataFrame,
                       instrument_id: int, **params) -> IndicatorResult:
        """
        Moving Average calculation requirements:
        - Support period and ma_type ('sma' or 'ema') parameters
        - Calculate appropriate moving average type
        - Handle edge cases for insufficient data
        - Return single MA value with trend indication
        """
        try:
            # Validate market data
            self._validate_market_data(market_data)
            
            # Get parameters - handle both single period and multiple periods
            periods = params.get('periods', params.get('period', 20))
            ma_type = params.get('ma_type', 'sma')
            
            # Normalize periods to list
            if isinstance(periods, int):
                periods = [periods]
            elif not isinstance(periods, list):
                periods = [20]  # Fallback
            
            # Filter periods that have sufficient data
            available_data_points = len(market_data)
            valid_periods = [p for p in periods if p <= available_data_points - 1]
            
            if not valid_periods:
                raise ValueError(f"Insufficient data for MA calculation: need at least {min(periods) + 1}, got {available_data_points}")
            
            # Use only valid periods
            periods = valid_periods
            
            # Calculate moving averages
            values = {}
            
            for period in periods:
                if ma_type.lower() == 'ema':
                    ma_series = self._calculate_ema(market_data['close'], period)
                else:
                    ma_series = self._calculate_sma(market_data['close'], period)
                
                current_ma = self._safe_iloc(ma_series, -1, market_data['close'].iloc[-1])
                values[f'ma_{period}'] = float(current_ma)
            
            # If single period, also add generic 'ma' key for backward compatibility
            if len(periods) == 1:
                values['ma'] = values[f'ma_{periods[0]}']
            
            # Build result with same structure as original
            return IndicatorResult(
                indicator_type=TechnicalIndicator.MOVING_AVERAGE,
                timestamp=self._calculate_timestamp(),
                instrument_id=instrument_id,
                values=values,
                metadata={
                    'periods': periods if len(periods) > 1 else periods[0],
                    'ma_type': ma_type
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error calculating Moving Average",
                instrument_id=instrument_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Default MA parameters matching original implementation."""
        return {
            'period': 20,
            'ma_type': 'sma'
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate Moving Average parameters."""
        # Handle both period and periods
        periods = params.get('periods', params.get('period'))
        ma_type = params.get('ma_type', 'sma')
        
        # Normalize periods to list
        if isinstance(periods, int):
            periods = [periods]
        elif not isinstance(periods, list):
            return False
        
        # Check all periods are valid integers
        if not all(isinstance(p, int) and 1 <= p <= 200 for p in periods):
            return False
        
        # Check ma_type is valid
        if ma_type.lower() not in ['sma', 'ema']:
            return False
        
        return True
    
    def get_minimum_data_points(self) -> int:
        """MA needs at least period + 1 data points."""
        return 21  # Conservative estimate for default period
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average using identical logic to original method.
        
        This method is copied exactly from AnalyticsEngine._calculate_sma to ensure
        mathematical compatibility and identical results.
        """
        return prices.rolling(window=period).mean()
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: Price series
            period: EMA period
            
        Returns:
            EMA series
        """
        return prices.ewm(span=period).mean()