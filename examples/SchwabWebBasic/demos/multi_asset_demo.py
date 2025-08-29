"""
Multi-asset demonstration module.

This module showcases the schwab-package's ability to handle different asset types
including equities, ETFs, futures, indices, and forex, demonstrating symbol detection,
cross-asset analysis, and asset-specific features.
"""

import asyncio
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

from ..utils.console_output import (
    print_demo_separator,
    print_success,
    print_error,
    print_warning,
    format_symbol_analysis,
    create_summary_table,
    create_progress_spinner
)
from ..utils.mock_data import (
    generate_mock_historical_data,
    generate_mock_symbol_analysis
)
from ..models.demo_config import DemoConfig


async def demo_asset_types(client, config: DemoConfig) -> None:
    """
    Demonstrate handling of different asset types.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Multi-Asset Type Demo")
    
    # Comprehensive asset type examples
    asset_examples = {
        'Equities': ['AAPL', 'MSFT', 'GOOGL'],
        'ETFs': ['SPY', 'QQQ', 'IWM'],
        'Futures': ['/ES', '/NQ', '/CL'],
        'Indices': ['$SPX', '$VIX', '$COMPX'],
        'Forex': ['EUR/USD', 'GBP/USD', 'USD/JPY']
    }
    
    print("🌐 Analyzing different asset classes:")
    for asset_type, symbols in asset_examples.items():
        print(f"  {asset_type}: {', '.join(symbols)}")
    
    results_by_type = {}
    
    with create_progress_spinner() as progress:
        total_symbols = sum(len(symbols) for symbols in asset_examples.values())
        task = progress.add_task("Analyzing asset types...", total=total_symbols)
        
        for asset_type, symbols in asset_examples.items():
            type_results = []
            
            for symbol in symbols:
                try:
                    # Get symbol analysis
                    if config.mock_mode:
                        analysis = generate_mock_symbol_analysis(symbol)
                    else:
                        analysis = client.analyze_symbol(symbol)
                    
                    # Get basic historical data
                    try:
                        if config.mock_mode:
                            df = generate_mock_historical_data(symbol, "daily", 10)
                        else:
                            start_date = datetime.now() - timedelta(days=10)
                            df = await client.get_historical_data(symbol, "daily", start_date)
                        
                        data_available = df is not None and not df.empty
                        latest_price = df['close'].iloc[-1] if data_available else None
                    except:
                        data_available = False
                        latest_price = None
                    
                    type_results.append({
                        'symbol': symbol,
                        'analysis': analysis,
                        'data_available': data_available,
                        'latest_price': latest_price
                    })
                    
                    if config.verbose_output:
                        print(format_symbol_analysis(symbol, analysis))
                        if latest_price:
                            print(f"    Latest price: ${latest_price:.2f}")
                
                except Exception as e:
                    print_error(f"Failed to analyze {symbol}: {e}")
                    type_results.append({
                        'symbol': symbol,
                        'analysis': None,
                        'data_available': False,
                        'latest_price': None
                    })
                
                progress.advance(task)
                await asyncio.sleep(0.1)
            
            results_by_type[asset_type] = type_results
    
    # Create summary
    _display_asset_type_summary(results_by_type)
    
    print_success(f"Multi-asset analysis completed for {total_symbols} symbols")


async def demo_futures_equities(client, config: DemoConfig) -> None:
    """
    Demonstrate comparison between futures and their underlying equities.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Futures vs Equities Comparison")
    
    # Futures and their equity counterparts
    pairs = [
        ('/ES', 'SPY', 'S&P 500'),
        ('/NQ', 'QQQ', 'NASDAQ 100'),
        ('/RTY', 'IWM', 'Russell 2000')
    ]
    
    print("⚖️  Comparing futures contracts with equity ETFs:")
    
    comparison_results = []
    
    with create_progress_spinner() as progress:
        task = progress.add_task("Comparing pairs...", total=len(pairs))
        
        for future_symbol, equity_symbol, description in pairs:
            print(f"\n📊 Analyzing {description}:")
            print(f"  Future: {future_symbol}")
            print(f"  ETF:    {equity_symbol}")
            
            try:
                # Get data for both instruments
                future_data = await _get_instrument_data(client, future_symbol, config)
                equity_data = await _get_instrument_data(client, equity_symbol, config)
                
                comparison = _compare_instruments(
                    future_symbol, future_data,
                    equity_symbol, equity_data
                )
                
                comparison_results.append(comparison)
                
                if config.verbose_output:
                    _display_pair_comparison(comparison)
            
            except Exception as e:
                print_error(f"Comparison failed for {description}: {e}")
            
            progress.advance(task)
            await asyncio.sleep(0.1)
    
    # Summary table
    if comparison_results:
        summary_table = []
        for comp in comparison_results:
            summary_table.append({
                'Pair': f"{comp['future_symbol']} vs {comp['equity_symbol']}",
                'Future Price': f"${comp['future_price']:.2f}" if comp['future_price'] else 'N/A',
                'ETF Price': f"${comp['equity_price']:.2f}" if comp['equity_price'] else 'N/A',
                'Correlation': f"{comp['correlation']:.2f}" if comp['correlation'] else 'N/A',
                'Liquidity': comp['liquidity_comparison']
            })
        
        create_summary_table(summary_table, "Futures vs ETF Comparison")
    
    print_success("Futures vs equities comparison completed")


async def demo_symbol_detection(client, config: DemoConfig) -> None:
    """
    Demonstrate automatic symbol type detection and handling.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Symbol Detection & Auto-Classification")
    
    # Mix of symbols for detection testing
    test_symbols = [
        'AAPL',        # Clear equity
        'spy',         # ETF (lowercase)
        '/es',         # Future (lowercase)
        '$spx',        # Index (lowercase)
        'EUR/USD',     # Forex
        'TSLA',        # Another equity
        'INVALID123',  # Invalid symbol
        'XLE',         # Sector ETF
        '/CL',         # Commodity future
        '$VIX'         # Volatility index
    ]
    
    print(f"🔍 Testing symbol detection on {len(test_symbols)} symbols:")
    print(f"  Test set: {', '.join(test_symbols)}")
    
    detection_results = []
    
    with create_progress_spinner() as progress:
        task = progress.add_task("Detecting symbol types...", total=len(test_symbols))
        
        for symbol in test_symbols:
            try:
                # Detect symbol type
                if config.mock_mode:
                    analysis = generate_mock_symbol_analysis(symbol)
                else:
                    analysis = client.analyze_symbol(symbol)
                
                # Attempt to get data with appropriate parameters
                data_success, data_info = await _test_data_retrieval(client, symbol, analysis, config)
                
                detection_results.append({
                    'Original': symbol,
                    'Normalized': analysis['symbol'],
                    'Type': analysis['instrument_type'],
                    'Confidence': f"{analysis['confidence']:.1%}",
                    'Data Available': '✅' if data_success else '❌',
                    'Special Notes': _get_symbol_notes(analysis)
                })
                
                if config.verbose_output:
                    print(f"\n{symbol:>12} → {analysis['instrument_type']:>8} "
                          f"({analysis['confidence']:.1%} confidence)")
                    if data_info:
                        print(f"            Data: {data_info}")
            
            except Exception as e:
                print_error(f"Detection failed for {symbol}: {e}")
                detection_results.append({
                    'Original': symbol,
                    'Normalized': symbol,
                    'Type': 'ERROR',
                    'Confidence': 'N/A',
                    'Data Available': '❌',
                    'Special Notes': str(e)[:30] + '...' if len(str(e)) > 30 else str(e)
                })
            
            progress.advance(task)
            await asyncio.sleep(0.1)
    
    # Display results
    create_summary_table(detection_results, "Symbol Detection Results")
    
    # Statistics
    successful_detections = sum(1 for r in detection_results if r['Type'] != 'ERROR')
    high_confidence = sum(1 for r in detection_results 
                         if r['Confidence'] != 'N/A' and float(r['Confidence'].strip('%')) >= 90)
    
    print(f"\n📊 Detection Statistics:")
    print(f"  Successful: {successful_detections}/{len(test_symbols)} ({successful_detections/len(test_symbols)*100:.1f}%)")
    print(f"  High Confidence (≥90%): {high_confidence}/{successful_detections}")
    
    print_success("Symbol detection demo completed")


async def _get_instrument_data(client, symbol: str, config: DemoConfig) -> Dict[str, Any]:
    """Get comprehensive data for an instrument."""
    data = {'symbol': symbol}
    
    try:
        # Get analysis
        if config.mock_mode:
            data['analysis'] = generate_mock_symbol_analysis(symbol)
        else:
            data['analysis'] = client.analyze_symbol(symbol)
        
        # Get historical data
        if config.mock_mode:
            data['historical'] = generate_mock_historical_data(symbol, "daily", 30)
        else:
            start_date = datetime.now() - timedelta(days=30)
            data['historical'] = await client.get_historical_data(symbol, "daily", start_date)
        
        # Calculate basic metrics
        if data['historical'] is not None and not data['historical'].empty:
            df = data['historical']
            data['latest_price'] = df['close'].iloc[-1]
            data['avg_volume'] = df['volume'].mean()
            data['volatility'] = df['close'].pct_change().std()
        
    except Exception as e:
        data['error'] = str(e)
    
    return data


def _compare_instruments(future_symbol: str, future_data: Dict[str, Any],
                        equity_symbol: str, equity_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two related instruments."""
    comparison = {
        'future_symbol': future_symbol,
        'equity_symbol': equity_symbol,
        'future_price': future_data.get('latest_price'),
        'equity_price': equity_data.get('latest_price'),
        'correlation': None,
        'liquidity_comparison': 'Unknown'
    }
    
    # Calculate correlation if both have historical data
    future_hist = future_data.get('historical')
    equity_hist = equity_data.get('historical')
    
    if (future_hist is not None and not future_hist.empty and 
        equity_hist is not None and not equity_hist.empty):
        
        # Align dates and calculate correlation
        min_len = min(len(future_hist), len(equity_hist))
        if min_len > 5:
            future_returns = future_hist['close'].tail(min_len).pct_change().dropna()
            equity_returns = equity_hist['close'].tail(min_len).pct_change().dropna()
            
            if len(future_returns) > 3 and len(equity_returns) > 3:
                comparison['correlation'] = future_returns.corr(equity_returns)
    
    # Compare liquidity (volume)
    future_vol = future_data.get('avg_volume', 0)
    equity_vol = equity_data.get('avg_volume', 0)
    
    if future_vol and equity_vol:
        if future_vol > equity_vol:
            comparison['liquidity_comparison'] = 'Future > ETF'
        elif equity_vol > future_vol * 2:
            comparison['liquidity_comparison'] = 'ETF > Future'
        else:
            comparison['liquidity_comparison'] = 'Similar'
    
    return comparison


async def _test_data_retrieval(client, symbol: str, analysis: Dict[str, Any], 
                              config: DemoConfig) -> Tuple[bool, str]:
    """Test if data can be retrieved for a symbol."""
    try:
        if config.mock_mode:
            df = generate_mock_historical_data(symbol, "daily", 5)
        else:
            start_date = datetime.now() - timedelta(days=5)
            df = await client.get_historical_data(symbol, "daily", start_date)
        
        if df is not None and not df.empty:
            return True, f"{len(df)} records, latest: ${df['close'].iloc[-1]:.2f}"
        else:
            return False, "No data returned"
    
    except Exception as e:
        return False, f"Error: {str(e)[:50]}..."


def _display_asset_type_summary(results_by_type: Dict[str, List[Dict[str, Any]]]) -> None:
    """Display summary of asset type analysis."""
    print("\n📊 Asset Type Analysis Summary:")
    
    summary_data = []
    
    for asset_type, results in results_by_type.items():
        total_symbols = len(results)
        successful_analysis = sum(1 for r in results if r['analysis'] is not None)
        data_available = sum(1 for r in results if r['data_available'])
        
        avg_confidence = 0
        if successful_analysis > 0:
            confidences = [r['analysis']['confidence'] for r in results if r['analysis']]
            avg_confidence = sum(confidences) / len(confidences)
        
        summary_data.append({
            'Asset Type': asset_type,
            'Symbols': total_symbols,
            'Analysis Success': f"{successful_analysis}/{total_symbols}",
            'Data Available': f"{data_available}/{total_symbols}",
            'Avg Confidence': f"{avg_confidence:.1%}" if avg_confidence > 0 else 'N/A'
        })
    
    create_summary_table(summary_data, "Asset Type Summary")


def _display_pair_comparison(comparison: Dict[str, Any]) -> None:
    """Display detailed comparison between two instruments."""
    future_sym = comparison['future_symbol']
    equity_sym = comparison['equity_symbol']
    
    print(f"  📈 {future_sym}: ${comparison['future_price']:.2f}")
    print(f"  📊 {equity_sym}: ${comparison['equity_price']:.2f}")
    
    if comparison['correlation'] is not None:
        corr = comparison['correlation']
        if corr > 0.8:
            corr_desc = "Strong positive"
        elif corr > 0.5:
            corr_desc = "Moderate positive"
        elif corr > -0.5:
            corr_desc = "Weak"
        else:
            corr_desc = "Negative"
        print(f"  🔗 Correlation: {corr:.3f} ({corr_desc})")
    
    print(f"  💧 Liquidity: {comparison['liquidity_comparison']}")


def _get_symbol_notes(analysis: Dict[str, Any]) -> str:
    """Get special notes about a symbol."""
    notes = []
    
    if analysis.get('extended_hours_supported'):
        notes.append("Extended hours")
    
    if analysis.get('requires_special_handling'):
        notes.append("Special handling")
    
    confidence = analysis.get('confidence', 0)
    if confidence < 0.7:
        notes.append("Low confidence")
    
    return ', '.join(notes) if notes else 'Standard'