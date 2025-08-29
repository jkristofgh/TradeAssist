"""
Console output formatting utilities.

This module provides functions for pretty printing data frames, quotes,
symbol analysis, and other output formatting for enhanced user experience.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from tabulate import tabulate


# Rich console instance for colored output
console = Console()


def print_banner(title: str, subtitle: Optional[str] = None) -> None:
    """
    Print a formatted banner with title and optional subtitle.
    
    Args:
        title: Main title text
        subtitle: Optional subtitle text
    """
    if subtitle:
        content = f"[bold cyan]{title}[/bold cyan]\n[dim]{subtitle}[/dim]"
    else:
        content = f"[bold cyan]{title}[/bold cyan]"
    
    panel = Panel(
        content,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)


def print_success(message: str) -> None:
    """Print a success message in green."""
    console.print(f"✅ [green]{message}[/green]")


def print_error(message: str) -> None:
    """Print an error message in red."""
    console.print(f"❌ [red]{message}[/red]")


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    console.print(f"⚠️  [yellow]{message}[/yellow]")


def format_dataframe(df: pd.DataFrame, symbol: str, max_rows: int = 10) -> str:
    """
    Format a pandas DataFrame for console display.
    
    Args:
        df: DataFrame to format
        symbol: Symbol name for header
        max_rows: Maximum number of rows to display
        
    Returns:
        str: Formatted string representation
    """
    if df is None or df.empty:
        return f"No data available for {symbol}"
    
    # Limit rows for display
    display_df = df.tail(max_rows) if len(df) > max_rows else df.copy()
    
    # Format numeric columns
    for col in display_df.columns:
        if display_df[col].dtype in ['float64', 'float32']:
            if col.lower() in ['volume']:
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "N/A")
            else:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
    
    # Format index if it's datetime
    if hasattr(display_df.index, 'strftime'):
        display_df.index = display_df.index.strftime('%Y-%m-%d %H:%M')
    
    table_str = tabulate(
        display_df,
        headers=display_df.columns,
        tablefmt="grid",
        showindex=True
    )
    
    return f"\n📊 {symbol} Historical Data (showing last {len(display_df)} records):\n{table_str}"


def format_quote(symbol: str, data: Dict[str, Any]) -> str:
    """
    Format a real-time quote for console display.
    
    Args:
        symbol: Trading symbol
        data: Quote data dictionary
        
    Returns:
        str: Formatted quote string
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    last = data.get('last', 'N/A')
    bid = data.get('bid', 'N/A')
    ask = data.get('ask', 'N/A')
    volume = data.get('volume', 'N/A')
    change = data.get('change', 0)
    change_percent = data.get('change_percent', 0)
    
    # Format price change with color
    if isinstance(change_percent, (int, float)):
        if change_percent > 0:
            change_color = "green"
            change_symbol = "📈"
        elif change_percent < 0:
            change_color = "red"  
            change_symbol = "📉"
        else:
            change_color = "white"
            change_symbol = "➡️"
        
        change_str = f"[{change_color}]{change_symbol} {change_percent:+.2f}%[/{change_color}]"
    else:
        change_str = "➡️ N/A"
    
    # Format volume
    if isinstance(volume, (int, float)) and volume > 0:
        volume_str = f"{volume:,.0f}"
    else:
        volume_str = "N/A"
    
    return (f"[{timestamp}] {symbol:>6} | "
            f"Last: ${last} | Bid: ${bid} | Ask: ${ask} | "
            f"Vol: {volume_str} | {change_str}")


def format_symbol_analysis(symbol: str, analysis: Dict[str, Any]) -> str:
    """
    Format symbol analysis results for console display.
    
    Args:
        symbol: Trading symbol
        analysis: Analysis results dictionary
        
    Returns:
        str: Formatted analysis string
    """
    instrument_type = analysis.get('instrument_type', 'UNKNOWN')
    confidence = analysis.get('confidence', 0)
    
    # Get confidence color based on level
    if confidence >= 0.9:
        confidence_color = "green"
    elif confidence >= 0.7:
        confidence_color = "yellow"
    else:
        confidence_color = "red"
    
    confidence_str = f"[{confidence_color}]{confidence:.1%}[/{confidence_color}]"
    
    output = f"🔍 {symbol:>6} | Type: {instrument_type:>12} | Confidence: {confidence_str}"
    
    # Add additional info if available
    if analysis.get('extended_hours_supported'):
        output += " | ⏰ Extended Hours"
    
    if analysis.get('requires_special_handling'):
        output += " | ⚠️  Special Handling"
    
    return output


def format_technical_analysis(symbol: str, df: pd.DataFrame) -> str:
    """
    Format technical analysis results for console display.
    
    Args:
        symbol: Trading symbol
        df: DataFrame with OHLCV data
        
    Returns:
        str: Formatted technical analysis
    """
    if df is None or df.empty or len(df) < 20:
        return f"Insufficient data for technical analysis of {symbol}"
    
    latest = df.iloc[-1]
    
    # Calculate simple moving averages
    df_copy = df.copy()
    df_copy['sma_20'] = df_copy['close'].rolling(window=20).mean()
    df_copy['sma_50'] = df_copy['close'].rolling(window=50).mean() if len(df) >= 50 else None
    
    # Calculate RSI
    delta = df_copy['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_copy['rsi'] = 100 - (100 / (1 + rs))
    
    latest_analysis = df_copy.iloc[-1]
    
    # Format output
    output = f"\n📈 Technical Analysis for {symbol}:\n"
    output += f"  Current Price: ${latest['close']:.2f}\n"
    
    if pd.notnull(latest_analysis.get('sma_20')):
        output += f"  20-day SMA: ${latest_analysis['sma_20']:.2f}\n"
    
    if pd.notnull(latest_analysis.get('sma_50')):
        output += f"  50-day SMA: ${latest_analysis['sma_50']:.2f}\n"
    
    if pd.notnull(latest_analysis.get('rsi')):
        rsi = latest_analysis['rsi']
        if rsi > 70:
            rsi_signal = "[red]Overbought[/red]"
        elif rsi < 30:
            rsi_signal = "[green]Oversold[/green]"
        else:
            rsi_signal = "[white]Neutral[/white]"
        output += f"  RSI (14): {rsi:.1f} - {rsi_signal}\n"
    
    # Simple trend analysis
    if (pd.notnull(latest_analysis.get('sma_20')) and 
        pd.notnull(latest_analysis.get('sma_50'))):
        current = latest['close']
        sma_20 = latest_analysis['sma_20']
        sma_50 = latest_analysis['sma_50']
        
        if current > sma_20 > sma_50:
            trend = "[green]📈 Bullish Trend[/green]"
        elif current < sma_20 < sma_50:
            trend = "[red]📉 Bearish Trend[/red]"
        else:
            trend = "[yellow]➡️ Mixed Signals[/yellow]"
        
        output += f"  Trend: {trend}\n"
    
    return output


def create_summary_table(data: List[Dict[str, Any]], title: str) -> None:
    """
    Create and display a summary table using Rich.
    
    Args:
        data: List of dictionaries with table data
        title: Table title
    """
    if not data:
        print_warning(f"No data available for {title}")
        return
    
    table = Table(title=title, title_style="bold cyan")
    
    # Add columns based on first row keys
    if data:
        for key in data[0].keys():
            table.add_column(key.replace('_', ' ').title(), style="white")
        
        # Add rows
        for row in data:
            table.add_row(*[str(value) for value in row.values()])
    
    console.print(table)


def create_progress_spinner(description: str = "Processing..."):
    """
    Create a progress spinner context manager.
    
    Args:
        description: Description text for the spinner
        
    Returns:
        Progress context manager
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    )


def format_portfolio_summary(portfolio_data: Dict[str, Any]) -> str:
    """
    Format portfolio analysis summary.
    
    Args:
        portfolio_data: Dictionary with portfolio metrics
        
    Returns:
        str: Formatted portfolio summary
    """
    output = "\n💼 Portfolio Analysis Summary:\n"
    
    if 'annual_return' in portfolio_data:
        return_val = portfolio_data['annual_return']
        return_color = "green" if return_val > 0 else "red"
        output += f"  Annual Return: [{return_color}]{return_val:.2%}[/{return_color}]\n"
    
    if 'annual_volatility' in portfolio_data:
        output += f"  Annual Volatility: {portfolio_data['annual_volatility']:.2%}\n"
    
    if 'sharpe_ratio' in portfolio_data:
        sharpe = portfolio_data['sharpe_ratio']
        sharpe_color = "green" if sharpe > 1.0 else "yellow" if sharpe > 0.5 else "red"
        output += f"  Sharpe Ratio: [{sharpe_color}]{sharpe:.2f}[/{sharpe_color}]\n"
    
    if 'max_drawdown' in portfolio_data:
        drawdown = portfolio_data['max_drawdown']
        output += f"  Max Drawdown: [red]{drawdown:.2%}[/red]\n"
    
    return output


def print_demo_separator(demo_name: str) -> None:
    """Print a separator between different demos."""
    console.print(f"\n{'='*60}")
    console.print(f"🚀 Starting {demo_name}")
    console.print(f"{'='*60}\n")