"""
RSI (Relative Strength Index) calculation strategy.

This strategy implements the RSI technical indicator calculation using the same
mathematical approach as the original god method to ensure backward compatibility.
"""

import pandas as pd
import numpy as np
import structlog
from typing import Dict, Any
from datetime import datetime

from .base import IndicatorStrategy
from ...analytics_engine import IndicatorResult, TechnicalIndicator

logger = structlog.get_logger()


class RSIStrategy(IndicatorStrategy):
    """
    Relative Strength Index calculation strategy.
    
    Current Implementation Analysis:
    - Existing calculation in god method lines 285-301 (17 lines)
    - Uses pandas rolling average for gain/loss calculation
    - Default period: 14
    - Overbought threshold: 70, Oversold threshold: 30
    """
    
    async def calculate(self, market_data: pd.DataFrame, 
                       instrument_id: int, **params) -> IndicatorResult:
        """
        RSI calculation requirements:
        - Support period parameter (default: 14)
        - Validate minimum data points (period + 1)
        - Handle edge cases (all gains or all losses)
        - Return overbought/oversold levels
        - Maintain identical results to existing calculation
        """
        try:
            # Validate market data
            self._validate_market_data(market_data)
            
            # Get parameters
            period = params.get('period', 14)
            
            # Additional validation for RSI-specific requirements  
            if len(market_data) < period + 1:
                raise ValueError(f"Insufficient data for RSI calculation: need {period + 1}, got {len(market_data)}")
            
            # Calculate RSI using the same logic as original method
            rsi_series = self._calculate_rsi(market_data['close'], period)
            
            # Get the latest RSI value, handle NaN properly
            current_rsi = self._safe_iloc(rsi_series, -1, 50.0)
            
            # Handle NaN case (e.g., with constant prices)
            if pd.isna(current_rsi) or np.isinf(current_rsi):
                current_rsi = 50.0
            
            # Build result with same structure as original
            return IndicatorResult(
                indicator_type=TechnicalIndicator.RSI,
                timestamp=self._calculate_timestamp(),
                instrument_id=instrument_id,
                values={
                    'rsi': float(current_rsi),
                    'overbought': 70.0,
                    'oversold': 30.0
                },
                metadata={'period': period}
            )
            
        except Exception as e:
            logger.error(
                f"Error calculating RSI",
                instrument_id=instrument_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Default RSI parameters matching original implementation."""
        return {'period': 14}
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate period: 2 <= period <= 100"""
        period = params.get('period')
        if not isinstance(period, int):
            return False
        return 2 <= period <= 100
    
    def get_minimum_data_points(self) -> int:
        """RSI needs at least period + 1 data points."""
        return 15  # Default period (14) + 1
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index using identical logic to original method.
        
        This method is copied exactly from AnalyticsEngine._calculate_rsi to ensure
        mathematical compatibility and identical results.
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi