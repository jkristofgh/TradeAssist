"""
Symbol analysis and technical analysis demonstration module.

This module showcases symbol analysis, technical indicators, and portfolio
analysis capabilities using the schwab-package and pandas calculations.
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..utils.console_output import (
    print_demo_separator,
    print_success,
    print_error, 
    print_warning,
    format_symbol_analysis,
    format_technical_analysis,
    format_portfolio_summary,
    create_summary_table,
    create_progress_spinner
)
from ..utils.mock_data import (
    generate_mock_historical_data,
    generate_mock_symbol_analysis,
    generate_mock_portfolio_data
)
from ..models.demo_config import DemoConfig


async def demo_symbol_analysis(client, config: DemoConfig) -> None:
    """
    Demonstrate symbol analysis and instrument type detection.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Symbol Analysis & Instrument Detection")
    
    # Mix of different symbol types for analysis
    analysis_symbols = [
        "AAPL",      # Equity
        "SPY",       # ETF  
        "/ES",       # Future
        "$SPX",      # Index
        "EUR/USD"    # Forex
    ]
    
    print("🔍 Analyzing different instrument types...")
    
    analysis_results = []
    
    with create_progress_spinner() as progress:
        task = progress.add_task("Analyzing symbols...", total=len(analysis_symbols))
        
        for symbol in analysis_symbols:
            try:
                if config.mock_mode:
                    analysis = generate_mock_symbol_analysis(symbol)
                else:
                    analysis = client.analyze_symbol(symbol)
                
                analysis_results.append({
                    'Symbol': symbol,
                    'Type': analysis['instrument_type'],
                    'Confidence': f"{analysis['confidence']:.1%}",
                    'Extended Hours': "✅" if analysis.get('extended_hours_supported') else "❌",
                    'Special Handling': "⚠️" if analysis.get('requires_special_handling') else "✅"
                })
                
                if config.verbose_output:
                    print(format_symbol_analysis(symbol, analysis))
                
            except Exception as e:
                print_error(f"Analysis failed for {symbol}: {e}")
                analysis_results.append({
                    'Symbol': symbol,
                    'Type': 'ERROR',
                    'Confidence': 'N/A',
                    'Extended Hours': 'N/A',
                    'Special Handling': 'N/A'
                })
            
            progress.advance(task)
            await asyncio.sleep(0.1)
    
    # Display summary table
    create_summary_table(analysis_results, "Symbol Analysis Results")
    
    print_success(f"Analyzed {len(analysis_symbols)} symbols successfully")


async def demo_technical_analysis(client, config: DemoConfig) -> None:
    """
    Demonstrate technical analysis with various indicators.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Technical Analysis Demo")
    
    symbols = config.demo_symbols[:3]  # Analyze first 3 symbols
    lookback_days = config.analysis_config.lookback_days
    
    print(f"📊 Running technical analysis on {symbols}")
    print(f"📅 Lookback period: {lookback_days} days")
    
    technical_results = []
    
    with create_progress_spinner() as progress:
        task = progress.add_task("Computing technical indicators...", total=len(symbols))
        
        for symbol in symbols:
            try:
                # Get historical data
                if config.mock_mode:
                    df = generate_mock_historical_data(symbol, "daily", lookback_days)
                else:
                    start_date = datetime.now() - timedelta(days=lookback_days)
                    df = await client.get_historical_data(symbol, "daily", start_date)
                
                if df is None or df.empty:
                    print_warning(f"No data available for {symbol}")
                    continue
                
                # Calculate technical indicators
                indicators = _calculate_technical_indicators(df)
                
                # Generate signals
                signals = _generate_trading_signals(df, indicators)
                
                technical_results.append({
                    'Symbol': symbol,
                    'Price': f"${indicators['current_price']:.2f}",
                    'SMA20': f"${indicators['sma_20']:.2f}" if indicators['sma_20'] else 'N/A',
                    'RSI': f"{indicators['rsi']:.1f}" if indicators['rsi'] else 'N/A',
                    'Signal': signals['overall_signal'],
                    'Trend': signals['trend_direction']
                })
                
                if config.verbose_output:
                    print(format_technical_analysis(symbol, df))
                    print(f"  🎯 Signals: {signals}")
                
            except Exception as e:
                print_error(f"Technical analysis failed for {symbol}: {e}")
            
            progress.advance(task)
            await asyncio.sleep(0.1)
    
    # Display technical analysis summary
    if technical_results:
        create_summary_table(technical_results, "Technical Analysis Summary")
        
        # Count signals
        bullish_count = sum(1 for r in technical_results if 'Bullish' in r['Signal'])
        bearish_count = sum(1 for r in technical_results if 'Bearish' in r['Signal'])
        neutral_count = len(technical_results) - bullish_count - bearish_count
        
        print(f"\n📈 Signal Summary:")
        print(f"  Bullish: {bullish_count}")
        print(f"  Bearish: {bearish_count}")
        print(f"  Neutral: {neutral_count}")
    
    print_success("Technical analysis completed")


async def demo_portfolio_analysis(client, config: DemoConfig) -> None:
    """
    Demonstrate portfolio analysis with risk metrics.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Portfolio Analysis Demo")
    
    portfolio_weights = config.analysis_config.portfolio_weights
    symbols = list(portfolio_weights.keys())
    
    print(f"💼 Analyzing portfolio with {len(symbols)} positions")
    print("📊 Portfolio composition:")
    for symbol, weight in portfolio_weights.items():
        print(f"  {symbol}: {weight:.1%}")
    
    try:
        if config.mock_mode:
            portfolio_data = generate_mock_portfolio_data(symbols, portfolio_weights)
            print_warning("Using mock portfolio data")
        else:
            portfolio_data = await _calculate_portfolio_metrics(
                client, symbols, portfolio_weights, config.analysis_config.lookback_days
            )
        
        # Display portfolio metrics
        if portfolio_data:
            print(format_portfolio_summary(portfolio_data))
            
            # Create detailed table
            portfolio_table = [{
                'Metric': 'Annual Return',
                'Value': f"{portfolio_data.get('annual_return', 0):.2%}",
                'Description': 'Expected annual return'
            }, {
                'Metric': 'Annual Volatility', 
                'Value': f"{portfolio_data.get('annual_volatility', 0):.2%}",
                'Description': 'Annual price volatility'
            }, {
                'Metric': 'Sharpe Ratio',
                'Value': f"{portfolio_data.get('sharpe_ratio', 0):.2f}",
                'Description': 'Risk-adjusted return'
            }, {
                'Metric': 'Max Drawdown',
                'Value': f"{portfolio_data.get('max_drawdown', 0):.2%}",
                'Description': 'Worst decline from peak'
            }]
            
            create_summary_table(portfolio_table, "Portfolio Risk Metrics")
            
            # Risk assessment
            _assess_portfolio_risk(portfolio_data)
        
        print_success("Portfolio analysis completed")
        
    except Exception as e:
        print_error(f"Portfolio analysis failed: {e}")


def _calculate_technical_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate various technical indicators for a DataFrame.
    
    Args:
        df: OHLCV DataFrame
        
    Returns:
        Dict[str, Any]: Dictionary of calculated indicators
    """
    if df is None or df.empty or len(df) < 20:
        return {}
    
    indicators = {}
    
    # Current price
    indicators['current_price'] = df['close'].iloc[-1]
    
    # Simple Moving Averages
    if len(df) >= 20:
        df_copy = df.copy()
        df_copy['sma_20'] = df_copy['close'].rolling(window=20).mean()
        indicators['sma_20'] = df_copy['sma_20'].iloc[-1]
        
        if len(df) >= 50:
            df_copy['sma_50'] = df_copy['close'].rolling(window=50).mean()
            indicators['sma_50'] = df_copy['sma_50'].iloc[-1]
    
    # RSI
    if len(df) >= 14:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        indicators['rsi'] = rsi.iloc[-1]
    
    # MACD
    if len(df) >= 26:
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        indicators['macd'] = macd.iloc[-1]
        indicators['macd_signal'] = macd_signal.iloc[-1]
        indicators['macd_histogram'] = macd.iloc[-1] - macd_signal.iloc[-1]
    
    # Bollinger Bands
    if len(df) >= 20:
        sma_20 = df['close'].rolling(window=20).mean()
        std_20 = df['close'].rolling(window=20).std()
        indicators['bb_upper'] = (sma_20 + (std_20 * 2)).iloc[-1]
        indicators['bb_lower'] = (sma_20 - (std_20 * 2)).iloc[-1]
        indicators['bb_percent'] = ((df['close'].iloc[-1] - indicators['bb_lower']) / 
                                   (indicators['bb_upper'] - indicators['bb_lower']))
    
    return indicators


def _generate_trading_signals(df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate trading signals based on technical indicators.
    
    Args:
        df: OHLCV DataFrame
        indicators: Technical indicators dictionary
        
    Returns:
        Dict[str, str]: Trading signals
    """
    signals = {
        'trend_direction': 'Neutral',
        'momentum_signal': 'Neutral',
        'overall_signal': 'Neutral'
    }
    
    if not indicators:
        return signals
    
    current_price = indicators.get('current_price')
    sma_20 = indicators.get('sma_20')
    sma_50 = indicators.get('sma_50')
    rsi = indicators.get('rsi')
    macd = indicators.get('macd')
    macd_signal = indicators.get('macd_signal')
    
    # Trend analysis
    if sma_20 and sma_50 and current_price:
        if current_price > sma_20 > sma_50:
            signals['trend_direction'] = 'Bullish'
        elif current_price < sma_20 < sma_50:
            signals['trend_direction'] = 'Bearish'
        else:
            signals['trend_direction'] = 'Mixed'
    
    # Momentum analysis
    momentum_score = 0
    
    if rsi:
        if rsi > 70:
            momentum_score -= 1  # Overbought
        elif rsi < 30:
            momentum_score += 1  # Oversold
        elif 40 <= rsi <= 60:
            momentum_score += 0.5  # Neutral momentum
    
    if macd and macd_signal:
        if macd > macd_signal:
            momentum_score += 1
        else:
            momentum_score -= 1
    
    # Overall signal
    if momentum_score >= 1 and signals['trend_direction'] == 'Bullish':
        signals['overall_signal'] = 'Strong Bullish'
    elif momentum_score >= 0.5 and signals['trend_direction'] in ['Bullish', 'Mixed']:
        signals['overall_signal'] = 'Bullish'
    elif momentum_score <= -1 and signals['trend_direction'] == 'Bearish':
        signals['overall_signal'] = 'Strong Bearish'
    elif momentum_score <= -0.5 and signals['trend_direction'] in ['Bearish', 'Mixed']:
        signals['overall_signal'] = 'Bearish'
    else:
        signals['overall_signal'] = 'Neutral'
    
    return signals


async def _calculate_portfolio_metrics(client, symbols: List[str], 
                                     weights: Dict[str, float], 
                                     lookback_days: int) -> Dict[str, Any]:
    """
    Calculate portfolio risk metrics.
    
    Args:
        client: SchwabClient instance
        symbols: Portfolio symbols
        weights: Symbol weights
        lookback_days: Historical data period
        
    Returns:
        Dict[str, Any]: Portfolio metrics
    """
    # Get historical data for all symbols
    price_data = {}
    
    for symbol in symbols:
        try:
            start_date = datetime.now() - timedelta(days=lookback_days)
            df = await client.get_historical_data(symbol, "daily", start_date)
            if df is not None and not df.empty:
                price_data[symbol] = df['close']
        except Exception as e:
            print_warning(f"Failed to get data for {symbol}: {e}")
    
    if not price_data:
        return {}
    
    # Combine price data
    prices_df = pd.DataFrame(price_data)
    
    # Calculate returns
    returns = prices_df.pct_change().dropna()
    
    # Portfolio weights as array
    weight_array = np.array([weights.get(symbol, 0) for symbol in prices_df.columns])
    
    # Portfolio returns
    portfolio_returns = (returns * weight_array).sum(axis=1)
    
    # Calculate metrics
    annual_return = portfolio_returns.mean() * 252
    annual_volatility = portfolio_returns.std() * np.sqrt(252)
    sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
    
    # Max drawdown
    cumulative_returns = (1 + portfolio_returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min()
    
    return {
        'annual_return': annual_return,
        'annual_volatility': annual_volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'symbols': symbols,
        'weights': weights
    }


def _assess_portfolio_risk(portfolio_data: Dict[str, Any]) -> None:
    """
    Assess portfolio risk and provide recommendations.
    
    Args:
        portfolio_data: Portfolio metrics dictionary
    """
    print("\n🎯 Portfolio Risk Assessment:")
    
    sharpe_ratio = portfolio_data.get('sharpe_ratio', 0)
    annual_volatility = portfolio_data.get('annual_volatility', 0)
    max_drawdown = portfolio_data.get('max_drawdown', 0)
    
    # Sharpe ratio assessment
    if sharpe_ratio > 1.5:
        print("  📈 Excellent risk-adjusted returns (Sharpe > 1.5)")
    elif sharpe_ratio > 1.0:
        print("  ✅ Good risk-adjusted returns (Sharpe > 1.0)")
    elif sharpe_ratio > 0.5:
        print("  ⚠️  Moderate risk-adjusted returns (Sharpe > 0.5)")
    else:
        print("  ❌ Poor risk-adjusted returns (Sharpe < 0.5)")
    
    # Volatility assessment
    if annual_volatility < 0.15:
        print("  🛡️  Low volatility portfolio (< 15% annual)")
    elif annual_volatility < 0.25:
        print("  📊 Moderate volatility portfolio (15-25% annual)")
    else:
        print("  ⚡ High volatility portfolio (> 25% annual)")
    
    # Drawdown assessment
    if max_drawdown > -0.10:
        print("  💚 Low maximum drawdown (< 10%)")
    elif max_drawdown > -0.20:
        print("  💛 Moderate maximum drawdown (10-20%)")
    else:
        print("  🔴 High maximum drawdown (> 20%)")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if annual_volatility > 0.30:
        print("  • Consider reducing portfolio concentration")
    if sharpe_ratio < 0.5:
        print("  • Review asset allocation for better risk-adjusted returns")
    if max_drawdown < -0.25:
        print("  • Consider adding defensive assets to reduce drawdown risk")