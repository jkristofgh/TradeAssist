"""
Historical data demonstration module.

This module showcases historical data retrieval capabilities of the schwab-package,
demonstrating basic data fetching, multiple intervals, date ranges, and error handling.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from ..utils.console_output import (
    print_demo_separator, 
    print_success, 
    print_error, 
    print_warning,
    format_dataframe,
    create_progress_spinner
)
from ..utils.mock_data import generate_mock_historical_data
from ..models.demo_config import DemoConfig


async def demo_basic_historical(client, config: DemoConfig) -> None:
    """
    Demonstrate basic historical data retrieval.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Basic Historical Data Retrieval")
    
    symbols = config.get_enabled_symbols()[:3]  # Limit to first 3 symbols
    
    with create_progress_spinner() as progress:
        task = progress.add_task("Fetching historical data...", total=len(symbols))
        
        for symbol in symbols:
            try:
                if config.mock_mode:
                    print_warning(f"Using mock data for {symbol}")
                    df = generate_mock_historical_data(
                        symbol, 
                        config.default_interval, 
                        config.default_days_back
                    )
                else:
                    # Convert days back to start date
                    start_date = datetime.now() - timedelta(days=config.default_days_back)
                    df = await client.get_historical_data(
                        symbol, 
                        config.default_interval, 
                        start_date
                    )
                
                if df is not None and not df.empty:
                    print_success(f"Retrieved {len(df)} days of data for {symbol}")
                    
                    if config.verbose_output:
                        print(format_dataframe(df, symbol, max_rows=5))
                        
                        # Show some basic statistics
                        if len(df) > 1:
                            returns = df['close'].pct_change().dropna()
                            print(f"  📊 Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
                            print(f"  📈 Return: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1):.2%}")
                            print(f"  📉 Volatility: {returns.std():.2%}")
                            print(f"  📊 Avg Volume: {df['volume'].mean():,.0f}")
                else:
                    print_warning(f"No data received for {symbol}")
                    
            except Exception as e:
                print_error(f"Error fetching data for {symbol}: {e}")
            
            progress.advance(task)
            await asyncio.sleep(0.1)  # Brief pause between requests


async def demo_multiple_intervals(client, config: DemoConfig) -> None:
    """
    Demonstrate data retrieval across multiple time intervals.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Multiple Time Intervals Demo")
    
    symbol = config.demo_symbols[0]  # Use first symbol
    intervals = ["daily", "weekly"]
    
    # Add intraday intervals for equities
    if not symbol.startswith(('/', '$')):
        intervals.extend(["1h", "30m"])
    
    print(f"🔍 Analyzing {symbol} across different time intervals...")
    
    results = {}
    
    with create_progress_spinner() as progress:
        task = progress.add_task("Fetching data across intervals...", total=len(intervals))
        
        for interval in intervals:
            try:
                # Adjust days_back based on interval
                days_back = _get_days_back_for_interval(interval)
                
                if config.mock_mode:
                    df = generate_mock_historical_data(symbol, interval, days_back)
                else:
                    start_date = datetime.now() - timedelta(days=days_back)
                    df = await client.get_historical_data(symbol, interval, start_date)
                
                if df is not None and not df.empty:
                    results[interval] = df
                    print_success(f"{interval:>6}: {len(df)} records")
                    
                    if config.verbose_output:
                        latest = df.iloc[-1]
                        print(f"         Latest: ${latest['close']:.2f} (Vol: {latest['volume']:,})")
                else:
                    print_warning(f"No data for {interval}")
                    
            except Exception as e:
                print_error(f"Error with {interval}: {e}")
            
            progress.advance(task)
            await asyncio.sleep(0.1)
    
    # Compare intervals
    if len(results) > 1:
        print("\n📊 Interval Comparison:")
        for interval, df in results.items():
            if len(df) > 1:
                period_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
                avg_volume = df['volume'].mean()
                print(f"  {interval:>6}: {period_return:+6.2f}% return, {avg_volume:>10,.0f} avg volume")


async def demo_date_ranges(client, config: DemoConfig) -> None:
    """
    Demonstrate historical data retrieval with specific date ranges.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Date Range Queries Demo")
    
    symbol = config.demo_symbols[0]
    
    # Define different date ranges
    today = datetime.now()
    date_ranges = [
        {
            "name": "Last Week",
            "start": today - timedelta(days=7),
            "end": today,
            "days_back": 7
        },
        {
            "name": "Last Month", 
            "start": today - timedelta(days=30),
            "end": today,
            "days_back": 30
        },
        {
            "name": "Last Quarter",
            "start": today - timedelta(days=90),
            "end": today, 
            "days_back": 90
        }
    ]
    
    print(f"📅 Fetching {symbol} data for different date ranges...")
    
    with create_progress_spinner() as progress:
        task = progress.add_task("Processing date ranges...", total=len(date_ranges))
        
        for range_info in date_ranges:
            try:
                if config.mock_mode:
                    df = generate_mock_historical_data(
                        symbol, 
                        "daily", 
                        range_info["days_back"]
                    )
                else:
                    # Convert days back to start date
                    start_date = datetime.now() - timedelta(days=range_info["days_back"])
                    df = await client.get_historical_data(
                        symbol, 
                        "daily", 
                        start_date
                    )
                
                if df is not None and not df.empty:
                    print_success(f"{range_info['name']:>12}: {len(df)} trading days")
                    
                    if config.verbose_output and len(df) > 1:
                        start_price = df['close'].iloc[0]
                        end_price = df['close'].iloc[-1]
                        total_return = (end_price / start_price - 1) * 100
                        
                        date_start = df.index[0].strftime('%Y-%m-%d') if hasattr(df.index[0], 'strftime') else str(df.index[0])
                        date_end = df.index[-1].strftime('%Y-%m-%d') if hasattr(df.index[-1], 'strftime') else str(df.index[-1])
                        
                        print(f"             {date_start} to {date_end}")
                        print(f"             ${start_price:.2f} → ${end_price:.2f} ({total_return:+.2f}%)")
                else:
                    print_warning(f"No data for {range_info['name']}")
                    
            except Exception as e:
                print_error(f"Error with {range_info['name']}: {e}")
            
            progress.advance(task)
            await asyncio.sleep(0.1)


async def demo_error_handling(client, config: DemoConfig) -> None:
    """
    Demonstrate robust error handling for historical data requests.
    
    Args:
        client: SchwabClient instance or None for mock mode  
        config: Demo configuration
    """
    print_demo_separator("Error Handling Demo")
    
    # Test with various symbols including invalid ones
    test_symbols = ["AAPL", "INVALID_SYMBOL", "XYZ123", "$SPX"]
    
    print("🛡️  Testing error handling with various symbols...")
    
    successful_count = 0
    failed_count = 0
    
    for symbol in test_symbols:
        try:
            print(f"\n🔍 Testing {symbol}...")
            
            if config.mock_mode:
                # In mock mode, simulate some failures
                if "INVALID" in symbol or symbol == "XYZ123":
                    raise Exception(f"Mock error: Invalid symbol {symbol}")
                df = generate_mock_historical_data(symbol, "daily", 10)
            else:
                start_date = datetime.now() - timedelta(days=10)
                df = await client.get_historical_data(symbol, "daily", start_date)
            
            if df is not None and not df.empty:
                print_success(f"✅ {symbol}: {len(df)} records retrieved")
                successful_count += 1
            else:
                print_warning(f"⚠️  {symbol}: No data returned")
                failed_count += 1
                
        except Exception as e:
            print_error(f"❌ {symbol}: {str(e)}")
            failed_count += 1
        
        await asyncio.sleep(0.1)
    
    print(f"\n📊 Results Summary:")
    print(f"  ✅ Successful: {successful_count}")
    print(f"  ❌ Failed: {failed_count}")
    print(f"  📈 Success Rate: {(successful_count / len(test_symbols)) * 100:.1f}%")


def _get_days_back_for_interval(interval: str) -> int:
    """
    Get appropriate days_back parameter for different intervals.
    
    Args:
        interval: Data interval
        
    Returns:
        int: Number of periods to request
    """
    interval_map = {
        "1m": 60,      # 60 minutes
        "5m": 100,     # 100 5-minute bars
        "15m": 100,    # 100 15-minute bars  
        "30m": 100,    # 100 30-minute bars
        "1h": 100,     # 100 hours
        "daily": 50,   # 50 days
        "weekly": 52   # 52 weeks
    }
    
    return interval_map.get(interval, 30)


def _validate_symbol_for_interval(symbol: str, interval: str) -> bool:
    """
    Validate if a symbol supports a specific interval.
    
    Args:
        symbol: Trading symbol
        interval: Data interval
        
    Returns:
        bool: True if combination is valid
    """
    # Some basic validation rules
    if symbol.startswith('$') and interval in ["1m", "5m", "15m", "30m"]:
        return False  # Indices typically don't have minute data
    
    if '/' in symbol and len(symbol.split('/')) == 2:  # Forex
        if interval == "weekly":
            return False  # Forex might not have weekly data
    
    return True