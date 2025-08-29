"""
Mock data generation for testing without API access.

This module provides functions to generate realistic mock data for historical
prices, real-time quotes, and other market data to enable testing and
demonstration without requiring actual API credentials.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random


def generate_mock_historical_data(symbol: str, interval: str = "daily", 
                                days_back: int = 30) -> pd.DataFrame:
    """
    Generate mock historical OHLCV data for a symbol.
    
    Args:
        symbol: Trading symbol
        interval: Data interval (e.g., "daily", "1h", "30m")
        days_back: Number of periods to generate
        
    Returns:
        pd.DataFrame: Mock historical data with OHLCV columns
    """
    # Determine base price based on symbol type
    base_price = _get_base_price_for_symbol(symbol)
    
    # Generate date range
    end_date = datetime.now()
    if interval == "daily":
        freq = "D"
        start_date = end_date - timedelta(days=days_back)
    elif interval == "weekly":
        freq = "W"
        start_date = end_date - timedelta(weeks=days_back)
    elif interval == "1h":
        freq = "H"
        start_date = end_date - timedelta(hours=days_back)
    elif interval == "30m":
        freq = "30T"
        start_date = end_date - timedelta(minutes=days_back * 30)
    elif interval == "15m":
        freq = "15T"
        start_date = end_date - timedelta(minutes=days_back * 15)
    elif interval == "5m":
        freq = "5T"
        start_date = end_date - timedelta(minutes=days_back * 5)
    elif interval == "1m":
        freq = "T"
        start_date = end_date - timedelta(minutes=days_back)
    else:
        freq = "D"
        start_date = end_date - timedelta(days=days_back)
    
    # Create datetime index
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    # Filter out weekends for equity symbols (except forex)
    if not ("/" in symbol and len(symbol.split("/")) == 2):  # Not forex
        date_range = date_range[date_range.weekday < 5]
    
    if len(date_range) == 0:
        # Fallback to at least one data point
        date_range = pd.date_range(start=end_date - timedelta(days=1), end=end_date, freq="D")
    
    # Generate price series using random walk
    num_periods = len(date_range)
    returns = np.random.normal(0.0002, 0.02, num_periods)  # Small daily returns with volatility
    
    # Adjust volatility based on symbol type
    volatility_multiplier = _get_volatility_multiplier(symbol)
    returns *= volatility_multiplier
    
    # Create price series
    prices = [base_price]
    for i in range(1, num_periods):
        new_price = prices[-1] * (1 + returns[i])
        # Ensure price doesn't go negative
        prices.append(max(new_price, 0.01))
    
    # Generate OHLCV data
    data = []
    for i, (date, close_price) in enumerate(zip(date_range, prices)):
        # Generate realistic OHLC based on close price
        daily_vol = abs(returns[i]) * close_price * 2  # Daily range
        
        open_price = close_price * (1 + np.random.normal(0, 0.001))
        high_price = max(open_price, close_price) + random.uniform(0, daily_vol)
        low_price = min(open_price, close_price) - random.uniform(0, daily_vol)
        
        # Ensure logical price relationships
        high_price = max(high_price, open_price, close_price, low_price)
        low_price = min(low_price, open_price, close_price, high_price)
        
        # Generate volume based on symbol type
        base_volume = _get_base_volume_for_symbol(symbol)
        volume_multiplier = random.uniform(0.5, 2.0)  # Volume variation
        volume = int(base_volume * volume_multiplier)
        
        data.append({
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data, index=date_range)
    df.index.name = 'datetime'
    
    return df


def generate_mock_quote(symbol: str, base_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Generate a mock real-time quote for a symbol.
    
    Args:
        symbol: Trading symbol
        base_price: Base price to use (auto-generated if None)
        
    Returns:
        Dict[str, Any]: Mock quote data
    """
    if base_price is None:
        base_price = _get_base_price_for_symbol(symbol)
    
    # Generate realistic bid/ask spread
    spread_pct = _get_spread_percentage(symbol)
    spread = base_price * spread_pct
    
    last_price = base_price + random.uniform(-spread * 2, spread * 2)
    bid_price = last_price - spread / 2
    ask_price = last_price + spread / 2
    
    # Generate volume
    base_volume = _get_base_volume_for_symbol(symbol)
    volume = int(base_volume * random.uniform(0.8, 1.2))
    
    # Generate price change
    change = random.uniform(-0.05, 0.05) * last_price  # ±5% change
    change_percent = (change / last_price) * 100 if last_price > 0 else 0
    
    return {
        'last': round(last_price, 2),
        'bid': round(bid_price, 2),
        'ask': round(ask_price, 2),
        'volume': volume,
        'change': round(change, 2),
        'change_percent': round(change_percent, 2),
        'high': round(last_price * 1.02, 2),
        'low': round(last_price * 0.98, 2),
        'previous_close': round(last_price - change, 2),
        'timestamp': datetime.now().isoformat()
    }


def generate_mock_stream_event(symbol: str) -> Dict[str, Any]:
    """
    Generate a mock streaming event for real-time simulation.
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Dict[str, Any]: Mock stream event data
    """
    quote_data = generate_mock_quote(symbol)
    
    return {
        'symbol': symbol,
        'event_type': 'quote',
        'data': quote_data,
        'timestamp': datetime.now().isoformat()
    }


def generate_mock_symbol_analysis(symbol: str) -> Dict[str, Any]:
    """
    Generate mock symbol analysis results.
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Dict[str, Any]: Mock analysis results
    """
    instrument_type, confidence = _analyze_symbol_type(symbol)
    
    return {
        'symbol': symbol,
        'instrument_type': instrument_type,
        'confidence': confidence,
        'extended_hours_supported': instrument_type in ['EQUITY', 'ETF'],
        'requires_special_handling': instrument_type in ['FUTURE', 'INDEX', 'FOREX'],
        'data_limits': {
            'max_daily_lookback': 7300 if instrument_type in ['EQUITY', 'ETF'] else 1000,
            'max_minute_lookback': 48 if instrument_type in ['EQUITY', 'ETF'] else 30
        }
    }


def _get_base_price_for_symbol(symbol: str) -> float:
    """Get a realistic base price for a symbol."""
    symbol = symbol.upper()
    
    # Known symbols with approximate prices
    price_map = {
        'AAPL': 175.0,
        'MSFT': 380.0,
        'GOOGL': 140.0,
        'AMZN': 155.0,
        'TSLA': 250.0,
        'SPY': 470.0,
        'QQQ': 400.0,
        'IWM': 200.0,
        '/ES': 4700.0,
        '/NQ': 16000.0,
        '/RTY': 2000.0,
        '$SPX': 4700.0,
        '$VIX': 20.0,
        'EUR/USD': 1.08,
        'GBP/USD': 1.27,
        'USD/JPY': 148.0
    }
    
    if symbol in price_map:
        return price_map[symbol]
    
    # Generate price based on symbol type
    if symbol.startswith('/'):  # Futures
        return random.uniform(50.0, 5000.0)
    elif symbol.startswith('$'):  # Indices
        return random.uniform(100.0, 5000.0)
    elif '/' in symbol:  # Forex
        return random.uniform(0.5, 2.0)
    else:  # Equity/ETF
        return random.uniform(10.0, 500.0)


def _get_base_volume_for_symbol(symbol: str) -> int:
    """Get realistic base volume for a symbol."""
    symbol = symbol.upper()
    
    if symbol in ['AAPL', 'SPY', 'QQQ']:
        return random.randint(50_000_000, 100_000_000)
    elif symbol in ['MSFT', 'GOOGL', 'AMZN', 'TSLA']:
        return random.randint(20_000_000, 50_000_000)
    elif symbol.startswith('/'):  # Futures
        return random.randint(100_000, 500_000)
    elif '/' in symbol:  # Forex
        return random.randint(1_000_000, 10_000_000)
    else:  # Other equities
        return random.randint(1_000_000, 20_000_000)


def _get_volatility_multiplier(symbol: str) -> float:
    """Get volatility multiplier based on symbol type."""
    symbol = symbol.upper()
    
    if symbol == 'TSLA':
        return 2.0  # High volatility
    elif symbol in ['AAPL', 'MSFT', 'GOOGL']:
        return 1.2  # Moderate volatility
    elif symbol in ['SPY', 'QQQ', 'IWM']:
        return 0.8  # Lower volatility ETFs
    elif symbol.startswith('$') and 'VIX' in symbol:
        return 3.0  # Very high volatility
    elif symbol.startswith('/'):  # Futures
        return 1.5
    elif '/' in symbol:  # Forex
        return 0.5  # Lower forex volatility
    else:
        return 1.0


def _get_spread_percentage(symbol: str) -> float:
    """Get typical bid-ask spread percentage for symbol type."""
    symbol = symbol.upper()
    
    if symbol in ['AAPL', 'MSFT', 'SPY', 'QQQ']:
        return 0.0001  # 0.01% for liquid stocks
    elif symbol.startswith('/'):  # Futures
        return 0.0005  # 0.05%
    elif '/' in symbol:  # Forex
        return 0.00005  # 0.005% for major pairs
    else:
        return 0.0005  # 0.05% for other stocks


def _analyze_symbol_type(symbol: str) -> tuple[str, float]:
    """Analyze symbol to determine instrument type and confidence."""
    symbol = symbol.upper()
    
    if symbol.startswith('/'):
        return 'FUTURE', 0.95
    elif symbol.startswith('$'):
        return 'INDEX', 0.95
    elif '/' in symbol and len(symbol.split('/')) == 2:
        return 'FOREX', 0.95
    elif symbol in ['SPY', 'QQQ', 'IWM', 'GLD', 'TLT', 'XLF', 'XLE']:
        return 'ETF', 0.90
    elif len(symbol) >= 3 and symbol.isalpha():
        return 'EQUITY', 0.85
    else:
        return 'UNKNOWN', 0.50


def generate_mock_portfolio_data(symbols: List[str], weights: Dict[str, float]) -> Dict[str, Any]:
    """
    Generate mock portfolio analysis data.
    
    Args:
        symbols: List of portfolio symbols
        weights: Dictionary of symbol weights
        
    Returns:
        Dict[str, Any]: Mock portfolio metrics
    """
    # Generate mock returns
    annual_return = random.uniform(-0.1, 0.2)  # -10% to +20%
    annual_volatility = random.uniform(0.1, 0.3)  # 10% to 30%
    sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
    max_drawdown = random.uniform(-0.3, -0.05)  # -30% to -5%
    
    return {
        'annual_return': annual_return,
        'annual_volatility': annual_volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'symbols': symbols,
        'weights': weights,
        'total_symbols': len(symbols)
    }