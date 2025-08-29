"""
Main CLI application for the Schwab Package Demo.

This module provides the command-line interface for running various demonstrations
of the schwab-package library, including historical data, streaming, analysis,
and multi-asset examples.
"""

import asyncio
import sys
from typing import Optional

import click
from rich.prompt import Confirm, Prompt

from .demos import (
    demo_asset_types,
    demo_basic_historical,
    demo_basic_streaming,
    demo_date_ranges,
    demo_futures_equities,
    demo_market_scanner,
    demo_multiple_intervals,
    demo_portfolio_analysis,
    demo_price_alerts,
    demo_symbol_analysis,
    demo_symbol_detection,
    demo_technical_analysis,
)
from .utils.config import get_environment_info, load_config
from .utils.console_output import (
    console,
    print_banner,
    print_error,
    print_success,
    print_warning,
)


@click.group()
@click.version_option(version="1.0.0", prog_name="schwab-demo")
def cli():
    """
    Schwab Package Demo Application

    Comprehensive demonstrations of the schwab-package library for market data
    retrieval, real-time streaming, and financial analysis.
    """
    pass


@cli.command()
@click.option("--mock", is_flag=True, help="Use mock data instead of API calls")
@click.option("--verbose", is_flag=True, default=True, help="Enable verbose output")
@click.option("--demo", type=str, help="Run specific demo by name")
def run(mock: bool, verbose: bool, demo: Optional[str]):
    """Run the demo application with interactive menu or specific demo."""
    asyncio.run(_run_demo_app(mock, verbose, demo))


@cli.command()
def config():
    """Show current configuration and environment information."""
    _show_configuration()


@cli.command()
def list_demos():
    """List all available demonstrations."""
    _list_available_demos()


async def _run_demo_app(mock_mode: bool, verbose: bool, specific_demo: Optional[str]):
    """
    Main demo application runner.

    Args:
        mock_mode: Use mock data instead of API calls
        verbose: Enable verbose output
        specific_demo: Run a specific demo by name
    """
    # Welcome banner
    print_banner(
        "Schwab Package Demo Application",
        "Comprehensive demonstrations of schwab-package capabilities",
    )

    try:
        # Load configuration
        config = load_config()

        # Override mock mode if specified
        if mock_mode:
            config.mock_mode = True

        # Override verbose if specified
        if verbose is not None:
            config.verbose_output = verbose

        # Initialize client if not in mock mode
        client = None
        if not config.mock_mode:
            try:
                from schwab_package import SchwabClient

                client = SchwabClient(
                    api_key=config.api_key,
                    app_secret=config.app_secret,
                    callback_url=config.callback_url,
                )
                print_success("✅ Connected to Schwab API")
            except Exception as e:
                print_error(f"❌ Failed to connect to Schwab API: {e}")
                print_warning("🔄 Switching to mock mode")
                config.mock_mode = True
        else:
            print_warning("🎭 Running in mock mode - using simulated data")

        # Run specific demo or interactive menu
        if specific_demo:
            await _run_specific_demo(client, config, specific_demo)
        else:
            await _run_interactive_menu(client, config)

    except Exception as e:
        print_error(f"Application error: {e}")
        sys.exit(1)

    finally:
        if client:
            try:
                await client.close()
                print_success("🔌 Disconnected from Schwab API")
            except:
                pass


async def _run_interactive_menu(client, config):
    """Run the interactive demo selection menu."""
    demos = {
        "1": ("Historical Data - Basic", demo_basic_historical),
        "2": ("Historical Data - Multiple Intervals", demo_multiple_intervals),
        "3": ("Historical Data - Date Ranges", demo_date_ranges),
        "4": ("Real-time Streaming - Basic", demo_basic_streaming),
        "5": ("Real-time Streaming - Price Alerts", demo_price_alerts),
        "6": ("Real-time Streaming - Market Scanner", demo_market_scanner),
        "7": ("Symbol Analysis", demo_symbol_analysis),
        "8": ("Technical Analysis", demo_technical_analysis),
        "9": ("Portfolio Analysis", demo_portfolio_analysis),
        "10": ("Multi-Asset Types", demo_asset_types),
        "11": ("Futures vs Equities", demo_futures_equities),
        "12": ("Symbol Detection", demo_symbol_detection),
        "all": ("Run All Demos", "run_all"),
    }

    while True:
        # Display menu
        console.print("\n📋 Available Demonstrations:", style="bold cyan")
        for key, (name, _) in demos.items():
            console.print(f"  {key:>3}: {name}")
        console.print(f"  {'q':>3}: Quit")

        # Get user choice
        choice = Prompt.ask("\n🎯 Select demo", choices=list(demos.keys()) + ["q"])

        if choice == "q":
            print_success("👋 Thanks for using the Schwab Package Demo!")
            break

        if choice == "all":
            # Run all demos
            if Confirm.ask(
                "\n🚀 Run all demonstrations? This may take several minutes"
            ):
                for demo_key, (demo_name, demo_func) in demos.items():
                    if demo_key != "all":
                        console.print(f"\n{'=' * 60}")
                        console.print(f"🎯 Running: {demo_name}")
                        console.print(f"{'=' * 60}")
                        try:
                            await demo_func(client, config)
                        except Exception as e:
                            print_error(f"Demo failed: {e}")

                        if demo_key != "12":  # Not the last demo
                            input("\n⏸️  Press Enter to continue to next demo...")

                print_success("🎉 All demonstrations completed!")
        else:
            # Run selected demo
            demo_name, demo_func = demos[choice]
            console.print(f"\n🚀 Running: {demo_name}")
            try:
                await demo_func(client, config)
                print_success(f"✅ {demo_name} completed!")
            except Exception as e:
                print_error(f"❌ Demo failed: {e}")

        # Ask if user wants to continue
        if not Confirm.ask("\n🔄 Run another demo?", default=True):
            print_success("👋 Thanks for using the Schwab Package Demo!")
            break


async def _run_specific_demo(client, config, demo_name: str):
    """Run a specific demo by name."""
    demo_map = {
        "historical-basic": demo_basic_historical,
        "historical-intervals": demo_multiple_intervals,
        "historical-dates": demo_date_ranges,
        "streaming-basic": demo_basic_streaming,
        "streaming-alerts": demo_price_alerts,
        "streaming-scanner": demo_market_scanner,
        "symbol-analysis": demo_symbol_analysis,
        "technical-analysis": demo_technical_analysis,
        "portfolio-analysis": demo_portfolio_analysis,
        "asset-types": demo_asset_types,
        "futures-equities": demo_futures_equities,
        "symbol-detection": demo_symbol_detection,
    }

    if demo_name not in demo_map:
        print_error(f"Unknown demo: {demo_name}")
        print("Available demos:")
        for name in demo_map.keys():
            print(f"  - {name}")
        sys.exit(1)

    demo_func = demo_map[demo_name]
    console.print(f"🚀 Running: {demo_name}")

    try:
        await demo_func(client, config)
        print_success(f"✅ {demo_name} completed!")
    except Exception as e:
        print_error(f"❌ Demo failed: {e}")
        sys.exit(1)


def _show_configuration():
    """Display current configuration information."""
    print_banner("Configuration Information")

    try:
        env_info = get_environment_info()

        console.print("📁 Environment File:", style="bold")
        console.print(f"  .env exists: {'✅' if env_info['env_file_exists'] else '❌'}")

        console.print("\n🔐 Credentials:", style="bold")
        console.print(f"  API Key set: {'✅' if env_info['api_key_set'] else '❌'}")
        console.print(
            f"  App Secret set: {'✅' if env_info['app_secret_set'] else '❌'}"
        )
        console.print(f"  Callback URL: {env_info['callback_url']}")

        console.print("\n⚙️  Settings:", style="bold")
        console.print(f"  Mock Mode: {'✅' if env_info['mock_mode'] else '❌'}")
        console.print(
            f"  Verbose Output: {'✅' if env_info['verbose_output'] else '❌'}"
        )
        console.print(f"  Demo Symbols: {env_info['demo_symbols']}")

        # Try to load full configuration
        try:
            config = load_config()
            console.print("\n✅ Configuration validation: PASSED")

            if config.mock_mode:
                print_warning("⚠️  Running in mock mode - API credentials not required")
            else:
                print_success("🔗 Ready to connect to Schwab API")

        except Exception as e:
            console.print(f"\n❌ Configuration validation: FAILED")
            console.print(f"   Error: {e}")

            if not env_info["mock_mode"]:
                console.print("\n💡 Suggestions:")
                console.print("   1. Copy .env.example to .env")
                console.print("   2. Add your Schwab API credentials")
                console.print("   3. Or set MOCK_MODE=true for testing")

    except Exception as e:
        print_error(f"Failed to load configuration: {e}")


def _list_available_demos():
    """List all available demonstrations with descriptions."""
    print_banner("Available Demonstrations")

    demos = [
        (
            "Historical Data",
            [
                ("historical-basic", "Basic historical data retrieval"),
                ("historical-intervals", "Multiple time intervals"),
                ("historical-dates", "Custom date ranges"),
            ],
        ),
        (
            "Real-time Streaming",
            [
                ("streaming-basic", "Basic real-time quotes"),
                ("streaming-alerts", "Price alert system"),
                ("streaming-scanner", "Market scanner"),
            ],
        ),
        (
            "Analysis",
            [
                ("symbol-analysis", "Symbol type detection"),
                ("technical-analysis", "Technical indicators"),
                ("portfolio-analysis", "Portfolio risk metrics"),
            ],
        ),
        (
            "Multi-Asset",
            [
                ("asset-types", "Different asset classes"),
                ("futures-equities", "Futures vs ETF comparison"),
                ("symbol-detection", "Auto symbol classification"),
            ],
        ),
    ]

    for category, demo_list in demos:
        console.print(f"\n📊 {category}:", style="bold cyan")
        for demo_name, description in demo_list:
            console.print(f"  {demo_name:>20}: {description}")

    console.print(f"\n💡 Usage examples:")
    console.print(f"  schwab-demo run --demo historical-basic")
    console.print(f"  schwab-demo run --mock")
    console.print(f"  schwab-demo run --demo streaming-alerts --verbose")


async def main():
    """Async main function for running the application."""
    await _run_demo_app(mock_mode=False, verbose=True, specific_demo=None)


if __name__ == "__main__":
    # Support both CLI and direct execution
    if len(sys.argv) == 1:
        # No CLI arguments, run interactively
        asyncio.run(main())
    else:
        # Use CLI
        cli()
