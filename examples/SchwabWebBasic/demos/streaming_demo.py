"""
Real-time streaming demonstration module.

This module showcases real-time streaming capabilities of the schwab-package,
demonstrating basic streaming, price alerts, market scanning, and callback handling.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

from ..utils.console_output import (
    print_demo_separator,
    print_success, 
    print_error,
    print_warning,
    format_quote,
    create_progress_spinner
)
from ..utils.mock_data import generate_mock_stream_event
from ..models.demo_config import DemoConfig


async def demo_basic_streaming(client, config: DemoConfig) -> None:
    """
    Demonstrate basic real-time streaming.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Basic Real-time Streaming")
    
    symbols = config.streaming_config.symbols[:3]  # Limit to 3 symbols
    duration = min(config.streaming_config.duration, 30)  # Max 30 seconds for demo
    
    print(f"📡 Starting real-time stream for {symbols}")
    print(f"⏱️  Duration: {duration} seconds")
    print(f"🔄 Auto-reconnect: {config.streaming_config.auto_reconnect}")
    
    quote_count = 0
    
    def quote_callback(symbol: str, data: Dict[str, Any]):
        """Handle incoming quote updates."""
        nonlocal quote_count
        quote_count += 1
        
        if config.verbose_output:
            formatted_quote = format_quote(symbol, data)
            print(formatted_quote)
    
    try:
        if config.mock_mode:
            print_warning("Using mock streaming data")
            await _mock_streaming(symbols, quote_callback, duration)
        else:
            await client.stream_quotes(
                symbols=symbols,
                callback=quote_callback,
                duration=duration,
                auto_reconnect=config.streaming_config.auto_reconnect
            )
        
        print_success(f"Streaming completed. Received {quote_count} quote updates.")
        
    except Exception as e:
        print_error(f"Streaming error: {e}")


async def demo_price_alerts(client, config: DemoConfig) -> None:
    """
    Demonstrate price alert system using streaming data.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Price Alerts Demo")
    
    symbols = config.streaming_config.symbols[:2]  # Limit to 2 symbols
    duration = min(config.streaming_config.duration, 45)  # Max 45 seconds
    alert_threshold = config.streaming_config.alert_threshold
    
    print(f"🚨 Setting up price alerts for {symbols}")
    print(f"📊 Alert threshold: ±{alert_threshold:.1%}")
    
    # Track initial prices and alerts
    initial_prices = {}
    alert_count = 0
    
    def alert_callback(symbol: str, data: Dict[str, Any]):
        """Handle price alerts."""
        nonlocal alert_count
        
        current_price = data.get('last')
        if current_price is None:
            return
        
        # Set initial price on first quote
        if symbol not in initial_prices:
            initial_prices[symbol] = current_price
            print(f"📌 {symbol} baseline: ${current_price:.2f}")
            return
        
        # Calculate price change
        initial_price = initial_prices[symbol]
        price_change = (current_price - initial_price) / initial_price
        
        # Check alert threshold
        if abs(price_change) >= alert_threshold:
            alert_count += 1
            direction = "📈" if price_change > 0 else "📉"
            print(f"🚨 ALERT {alert_count}: {direction} {symbol} {price_change:+.2%} "
                  f"(${initial_price:.2f} → ${current_price:.2f})")
            
            # Update baseline to prevent spam
            initial_prices[symbol] = current_price
        
        if config.verbose_output:
            print(format_quote(symbol, data))
    
    try:
        if config.mock_mode:
            print_warning("Using mock streaming data")
            await _mock_streaming_with_alerts(symbols, alert_callback, duration, alert_threshold)
        else:
            await client.stream_quotes(
                symbols=symbols,
                callback=alert_callback,
                duration=duration
            )
        
        print_success(f"Price alerts completed. Triggered {alert_count} alerts.")
        
    except Exception as e:
        print_error(f"Price alert error: {e}")


async def demo_market_scanner(client, config: DemoConfig) -> None:
    """
    Demonstrate market scanning for significant moves and volume.
    
    Args:
        client: SchwabClient instance or None for mock mode
        config: Demo configuration
    """
    print_demo_separator("Market Scanner Demo")
    
    symbols = config.streaming_config.symbols
    duration = min(config.streaming_config.duration, 60)  # Max 60 seconds
    
    print(f"🔍 Market scanner monitoring {len(symbols)} symbols")
    print(f"📊 Scanning for significant moves and volume spikes")
    
    # Track price movements and volume
    price_tracker = defaultdict(deque)
    volume_tracker = defaultdict(deque)
    alerts_triggered = defaultdict(int)
    
    def scanner_callback(symbol: str, data: Dict[str, Any]):
        """Market scanner callback."""
        current_price = data.get('last')
        current_volume = data.get('volume', 0)
        change_percent = data.get('change_percent', 0)
        
        if current_price is None:
            return
        
        # Track price history (last 10 quotes)
        price_tracker[symbol].append(current_price)
        if len(price_tracker[symbol]) > 10:
            price_tracker[symbol].popleft()
        
        # Track volume history
        volume_tracker[symbol].append(current_volume)
        if len(volume_tracker[symbol]) > 10:
            volume_tracker[symbol].popleft()
        
        # Alert on significant price moves
        if isinstance(change_percent, (int, float)) and abs(change_percent) > 2.0:
            if alerts_triggered[f"{symbol}_price"] < 3:  # Limit alerts
                direction = "📈" if change_percent > 0 else "📉"
                print(f"🎯 MOVE ALERT: {direction} {symbol} {change_percent:+.2f}% "
                      f"@ ${current_price:.2f}")
                alerts_triggered[f"{symbol}_price"] += 1
        
        # Alert on volume spikes
        if len(volume_tracker[symbol]) >= 5:
            avg_volume = sum(list(volume_tracker[symbol])[:-1]) / (len(volume_tracker[symbol]) - 1)
            if current_volume > avg_volume * 2 and avg_volume > 0:
                if alerts_triggered[f"{symbol}_volume"] < 2:  # Limit alerts
                    print(f"🔊 VOLUME ALERT: {symbol} - Current: {current_volume:,} "
                          f"(Avg: {avg_volume:,.0f})")
                    alerts_triggered[f"{symbol}_volume"] += 1
        
        # Show periodic updates for active symbols
        if len(price_tracker[symbol]) > 1:
            price_momentum = (current_price - price_tracker[symbol][0]) / price_tracker[symbol][0]
            if abs(price_momentum) > 0.01 and config.verbose_output:  # > 1% move
                momentum_icon = "🔥" if abs(price_momentum) > 0.02 else "📊"
                print(f"{momentum_icon} {symbol}: ${current_price:.2f} "
                      f"({price_momentum:+.2%} momentum)")
    
    try:
        if config.mock_mode:
            print_warning("Using mock scanning data")
            await _mock_market_scanner(symbols, scanner_callback, duration)
        else:
            await client.stream_quotes(
                symbols=symbols,
                callback=scanner_callback,
                duration=duration
            )
        
        # Summary
        total_alerts = sum(alerts_triggered.values())
        active_symbols = len([s for s in symbols if len(price_tracker[s]) > 0])
        
        print_success(f"Market scan completed:")
        print(f"  📊 Monitored: {active_symbols} symbols")
        print(f"  🚨 Alerts: {total_alerts}")
        print(f"  📈 Most active: {_get_most_active_symbol(price_tracker)}")
        
    except Exception as e:
        print_error(f"Market scanner error: {e}")


async def _mock_streaming(symbols: List[str], callback, duration: int) -> None:
    """
    Mock streaming implementation for testing.
    
    Args:
        symbols: List of symbols to stream
        callback: Callback function for quotes
        duration: Streaming duration in seconds
    """
    end_time = datetime.now() + timedelta(seconds=duration)
    quote_interval = 1.0  # 1 second between quotes
    
    while datetime.now() < end_time:
        for symbol in symbols:
            event = generate_mock_stream_event(symbol)
            callback(symbol, event['data'])
            await asyncio.sleep(quote_interval / len(symbols))
        
        await asyncio.sleep(0.1)


async def _mock_streaming_with_alerts(symbols: List[str], callback, 
                                    duration: int, alert_threshold: float) -> None:
    """
    Mock streaming with simulated price alerts.
    
    Args:
        symbols: List of symbols to stream
        callback: Callback function
        duration: Duration in seconds
        alert_threshold: Alert threshold percentage
    """
    end_time = datetime.now() + timedelta(seconds=duration)
    base_prices = {}
    
    # Initialize base prices
    for symbol in symbols:
        event = generate_mock_stream_event(symbol)
        base_prices[symbol] = event['data']['last']
    
    while datetime.now() < end_time:
        for symbol in symbols:
            event = generate_mock_stream_event(symbol)
            
            # Occasionally create significant moves for alerts
            if datetime.now().second % 10 == 0:  # Every 10 seconds
                base_price = base_prices[symbol]
                # Simulate significant move
                move_size = alert_threshold * 1.5 * (1 if datetime.now().second % 20 == 0 else -1)
                event['data']['last'] = base_price * (1 + move_size)
                event['data']['change_percent'] = move_size * 100
            
            callback(symbol, event['data'])
            await asyncio.sleep(1.0)


async def _mock_market_scanner(symbols: List[str], callback, duration: int) -> None:
    """
    Mock market scanner with simulated activity.
    
    Args:
        symbols: List of symbols to scan
        callback: Scanner callback function
        duration: Duration in seconds
    """
    end_time = datetime.now() + timedelta(seconds=duration)
    
    while datetime.now() < end_time:
        for symbol in symbols:
            event = generate_mock_stream_event(symbol)
            
            # Simulate occasional significant moves
            if datetime.now().second % 15 == 0:  # Every 15 seconds
                event['data']['change_percent'] = 2.5 * (1 if datetime.now().second % 30 == 0 else -1)
            
            # Simulate volume spikes
            if datetime.now().second % 20 == 0:  # Every 20 seconds
                event['data']['volume'] *= 3
            
            callback(symbol, event['data'])
            await asyncio.sleep(0.5)


def _get_most_active_symbol(price_tracker: Dict[str, deque]) -> str:
    """
    Get the symbol with the most price updates.
    
    Args:
        price_tracker: Dictionary tracking price updates per symbol
        
    Returns:
        str: Most active symbol name
    """
    if not price_tracker:
        return "None"
    
    most_active = max(price_tracker.keys(), key=lambda k: len(price_tracker[k]))
    return f"{most_active} ({len(price_tracker[most_active])} updates)"