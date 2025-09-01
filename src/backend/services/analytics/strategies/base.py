"""
Base strategy interface for technical indicator calculations.

This module defines the abstract base class that all indicator strategies
must implement, ensuring consistent interfaces and behavior across all
technical indicators.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime


class IndicatorStrategy(ABC):
    """
    Base strategy interface for technical indicator calculations.
    
    Requirements:
    - Abstract method for indicator calculation
    - Parameter validation and default parameter management
    - Error handling integration with existing patterns
    - Performance benchmarking integration
    - Metadata and result structure standardization
    """
    
    @abstractmethod
    async def calculate(self, market_data: pd.DataFrame, 
                       instrument_id: int, **params) -> 'IndicatorResult':
        """
        Calculate technical indicator with standardized result format.
        
        Args:
            market_data: Historical market data with OHLCV columns
            instrument_id: ID of the instrument being analyzed
            **params: Indicator-specific parameters
            
        Returns:
            IndicatorResult: Calculated indicator with values and metadata
            
        Raises:
            ValueError: If market data is insufficient or invalid
            CalculationError: If indicator calculation fails
        """
        pass
        
    @abstractmethod  
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        Return indicator-specific default parameters.
        
        Returns:
            Dict containing default parameter values for this indicator
        """
        pass
        
    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Validate indicator-specific parameters.
        
        Args:
            params: Parameter dictionary to validate
            
        Returns:
            bool: True if parameters are valid, False otherwise
        """
        pass
    
    def get_supported_timeframes(self) -> List[str]:
        """
        Return supported timeframes for this indicator.
        
        Returns:
            List of supported timeframe strings
        """
        return ["1min", "5min", "15min", "30min", "1hour", "1day"]
    
    def get_minimum_data_points(self) -> int:
        """
        Return minimum data points needed for calculation.
        
        Returns:
            Minimum number of data points required
        """
        return 20  # Default, can be overridden
    
    def _validate_market_data(self, market_data: pd.DataFrame) -> None:
        """
        Validate market data has required columns and sufficient data.
        
        Args:
            market_data: Market data DataFrame to validate
            
        Raises:
            ValueError: If data is invalid or insufficient
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in market_data.columns]
        
        if missing_columns:
            raise ValueError(f"Market data missing required columns: {missing_columns}")
        
        if len(market_data) < self.get_minimum_data_points():
            raise ValueError(
                f"Insufficient data points: {len(market_data)} < {self.get_minimum_data_points()}"
            )
        
        # Check for NaN values in critical columns
        critical_columns = ['high', 'low', 'close']
        for col in critical_columns:
            if market_data[col].isna().any():
                raise ValueError(f"Market data contains NaN values in {col} column")
    
    def _calculate_timestamp(self) -> datetime:
        """
        Calculate standardized timestamp for indicator result.
        
        Returns:
            UTC timestamp for the calculation
        """
        return datetime.utcnow()
    
    def _safe_iloc(self, series: pd.Series, index: int, default: float = 0.0) -> float:
        """
        Safely get value from series with fallback.
        
        Args:
            series: Pandas series to extract value from
            index: Index to extract (typically -1 for last value)
            default: Default value if series is empty or index invalid
            
        Returns:
            Float value from series or default
        """
        try:
            if len(series) == 0:
                return default
            return float(series.iloc[index])
        except (IndexError, TypeError, ValueError):
            return default