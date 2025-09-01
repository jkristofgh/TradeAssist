"""
Bollinger Bands calculation strategy.

This strategy implements the Bollinger Bands technical indicator calculation using the same
mathematical approach as the original god method to ensure backward compatibility.
"""

import pandas as pd
import structlog
from typing import Dict, Any, Tuple
from datetime import datetime

from .base import IndicatorStrategy
from ...analytics_engine import IndicatorResult, TechnicalIndicator

logger = structlog.get_logger()


class BollingerStrategy(IndicatorStrategy):
    """
    Bollinger Bands calculation strategy.
    
    Current Implementation Analysis:
    - Existing calculation in god method lines 326-342 (17 lines)
    - Three bands: Upper, Middle (SMA), Lower
    - Default parameters: period=20, std_dev=2.0
    - Bandwidth and %B calculations included
    """
    
    async def calculate(self, market_data: pd.DataFrame,
                       instrument_id: int, **params) -> IndicatorResult:
        """
        Bollinger Bands calculation requirements:
        - Support period and std_dev parameters
        - Calculate middle band (Simple Moving Average)
        - Calculate upper/lower bands (middle ± std_dev * standard deviation)
        - Calculate bandwidth ((upper - lower) / middle)
        - Calculate %B ((price - lower) / (upper - lower))
        """
        try:
            # Validate market data
            self._validate_market_data(market_data)
            
            # Get parameters
            period = params.get('period', 20)
            std_dev = params.get('std_dev', 2.0)
            
            # Additional validation for Bollinger-specific requirements
            if len(market_data) < period + 1:
                raise ValueError(f"Insufficient data for Bollinger Bands calculation: need {period + 1}, got {len(market_data)}")
            
            # Calculate Bollinger Bands using the same logic as original method
            upper_band, middle_band, lower_band = self._calculate_bollinger_bands(
                market_data['close'], period, std_dev
            )
            
            # Get current price and band values
            current_price = market_data['close'].iloc[-1]
            current_upper = self._safe_iloc(upper_band, -1, current_price)
            current_middle = self._safe_iloc(middle_band, -1, current_price)
            current_lower = self._safe_iloc(lower_band, -1, current_price)
            
            # Calculate bandwidth
            bandwidth = 0.0
            if current_middle != 0:
                bandwidth = ((current_upper - current_lower) / current_middle) * 100
            
            # Build result with same structure as original
            return IndicatorResult(
                indicator_type=TechnicalIndicator.BOLLINGER_BANDS,
                timestamp=self._calculate_timestamp(),
                instrument_id=instrument_id,
                values={
                    'upper_band': float(current_upper),
                    'middle_band': float(current_middle),
                    'lower_band': float(current_lower),
                    'bandwidth': float(bandwidth)
                },
                metadata={
                    'period': period,
                    'std_dev': std_dev
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error calculating Bollinger Bands",
                instrument_id=instrument_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Default Bollinger Bands parameters matching original implementation."""
        return {
            'period': 20,
            'std_dev': 2.0
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate Bollinger Bands parameters."""
        period = params.get('period')
        std_dev = params.get('std_dev')
        
        # Check period is integer
        if not isinstance(period, int):
            return False
        
        # Check std_dev is number
        if not isinstance(std_dev, (int, float)):
            return False
        
        # Check reasonable ranges
        if not (2 <= period <= 100):
            return False
        if not (0.1 <= std_dev <= 5.0):
            return False
        
        return True
    
    def get_minimum_data_points(self) -> int:
        """Bollinger Bands needs at least period + 1 data points."""
        return 21  # Default period (20) + 1
    
    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands using identical logic to original method.
        
        This method is copied exactly from AnalyticsEngine._calculate_bollinger_bands to ensure
        mathematical compatibility and identical results.
        """
        middle_band = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        return upper_band, middle_band, lower_band