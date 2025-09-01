"""
Analytics strategy pattern implementations.

This package contains the strategy pattern infrastructure for technical
indicator calculations, replacing the monolithic _calculate_indicator method
with focused, testable strategy classes.
"""

from .base import IndicatorStrategy
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .bollinger_strategy import BollingerStrategy
from .moving_average_strategy import MovingAverageStrategy
from .stochastic_strategy import StochasticStrategy
from .atr_strategy import ATRStrategy

__all__ = [
    'IndicatorStrategy',
    'RSIStrategy',
    'MACDStrategy',
    'BollingerStrategy',
    'MovingAverageStrategy',
    'StochasticStrategy',
    'ATRStrategy'
]