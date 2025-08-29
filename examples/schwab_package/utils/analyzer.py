"""
Symbol analysis and instrument type detection utility.

Provides intelligent symbol parsing to determine instrument types and apply
appropriate data handling logic for different asset classes.
"""

import re
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Any

from ..models import InstrumentType


class SymbolPattern(str, Enum):
    """Symbol pattern types for detection."""

    EQUITY = "equity"
    INDEX = "index"
    FUTURES = "futures"
    ETF = "etf"
    FOREX = "forex"
    OPTION = "option"
    CRYPTO = "crypto"
    UNKNOWN = "unknown"


@dataclass
class InstrumentProfile:
    """Profile containing instrument-specific metadata and limits."""

    instrument_type: InstrumentType
    pattern_type: SymbolPattern
    confidence: float  # 0.0 to 1.0

    # Data availability limits
    max_minute_lookback: timedelta
    max_daily_lookback: timedelta
    default_interval_days: int

    # API-specific settings
    extended_hours_supported: bool
    requires_special_handling: bool

    # Display metadata
    description: str
    examples: list[str]

    # Optional fields with defaults
    api_method_override: str | None = None


class SymbolAnalyzer:
    """
    Intelligent symbol analyzer for determining instrument types and characteristics.

    Uses pattern matching, known symbol lists, and heuristics to classify symbols
    and provide appropriate data handling recommendations.
    """

    # Known index symbols and patterns
    INDEX_SYMBOLS = {
        "SPX",
        "$SPX",  # S&P 500 Index
        "NDX",
        "$NDX",  # NASDAQ 100 Index
        "RUT",
        "$RUT",  # Russell 2000 Index
        "DJI",
        "$DJI",  # Dow Jones Index
        "VIX",
        "$VIX",  # Volatility Index
        "TNX",
        "$TNX",  # 10-Year Treasury
    }

    # Known major ETF symbols
    ETF_SYMBOLS = {
        "SPY",
        "QQQ",
        "IWM",
        "EFA",
        "EEM",
        "VTI",
        "ARKK",
        "ARKQ",
        "ARKW",
        "XLF",
        "XLE",
        "XLK",
        "XLV",
        "XLI",
        "XLP",
        "XLU",
        "XLB",
        "XLRE",
        "GLD",
        "SLV",
        "USO",
        "UNG",
        "TLT",
        "IEF",
        "SHY",
        "HYG",
        "LQD",
        "VOO",
        "VEA",
        "VWO",
        "BND",
        "VTEB",
        "VXUS",
        "VNQ",
        "VGT",
        "VHT",
    }

    # Futures contract patterns
    FUTURES_PATTERNS = [
        r"^/[A-Z]{1,2}$",  # /ES, /NQ, /YM, /RTY
        r"^[A-Z]{1,3}[FGHJKMNQUVXZ]\d{2}$",  # CLM23, ESU23, GCZ23
        r"^[A-Z]{2,3}\d{4}$",  # CL2023, ES2023
    ]

    # Forex patterns
    FOREX_PATTERNS = [
        r"^[A-Z]{3}/[A-Z]{3}$",  # EUR/USD, GBP/JPY
        r"^[A-Z]{6}$",  # EURUSD, GBPJPY
    ]

    # Crypto patterns
    CRYPTO_PATTERNS = [
        r"^[A-Z]{3,4}-USD$",  # BTC-USD, ETH-USD
        r"^[A-Z]{3,4}USD$",  # BTCUSD, ETHUSD
    ]

    # Option patterns (OCC format)
    OPTION_PATTERNS = [
        r"^[A-Z]{1,5}\d{6}[CP]\d{8}$",  # Standard OCC format
        r"^[A-Z]{1,5}\d{2}[01]\d[01]\d[CP]\d+$",  # Alternative format
    ]

    def __init__(self) -> None:
        """Initialize the symbol analyzer with predefined profiles."""
        self._profiles = self._create_instrument_profiles()

    def _create_instrument_profiles(self) -> dict[InstrumentType, InstrumentProfile]:
        """Create predefined instrument profiles with data limits and characteristics."""
        return {
            InstrumentType.EQUITY: InstrumentProfile(
                instrument_type=InstrumentType.EQUITY,
                pattern_type=SymbolPattern.EQUITY,
                confidence=0.8,
                max_minute_lookback=timedelta(days=48),
                max_daily_lookback=timedelta(days=365 * 20),
                default_interval_days=365,
                extended_hours_supported=True,
                requires_special_handling=False,
                description="Common stocks and equity securities",
                examples=["AAPL", "MSFT", "GOOGL", "TSLA"],
            ),
            InstrumentType.ETF: InstrumentProfile(
                instrument_type=InstrumentType.ETF,
                pattern_type=SymbolPattern.ETF,
                confidence=0.9,
                max_minute_lookback=timedelta(days=48),
                max_daily_lookback=timedelta(days=365 * 20),
                default_interval_days=365,
                extended_hours_supported=True,
                requires_special_handling=False,
                description="Exchange-traded funds",
                examples=["SPY", "QQQ", "IWM", "VTI"],
            ),
            InstrumentType.INDEX: InstrumentProfile(
                instrument_type=InstrumentType.INDEX,
                pattern_type=SymbolPattern.INDEX,
                confidence=0.95,
                max_minute_lookback=timedelta(days=48),
                max_daily_lookback=timedelta(days=365 * 25),
                default_interval_days=365 * 2,
                extended_hours_supported=False,  # Most indices don't trade extended hours
                requires_special_handling=True,
                description="Market indices and benchmarks",
                examples=["SPX", "$SPX", "NDX", "VIX"],
            ),
            InstrumentType.FUTURE: InstrumentProfile(
                instrument_type=InstrumentType.FUTURE,
                pattern_type=SymbolPattern.FUTURES,
                confidence=0.9,
                max_minute_lookback=timedelta(days=60),  # Futures have longer minute data
                max_daily_lookback=timedelta(days=365 * 10),
                default_interval_days=180,
                extended_hours_supported=True,
                requires_special_handling=True,
                description="Futures contracts",
                examples=["/ES", "/NQ", "CLM23", "GCZ23"],
                api_method_override="get_price_history",  # Futures may need different API method
            ),
            InstrumentType.FOREX: InstrumentProfile(
                instrument_type=InstrumentType.FOREX,
                pattern_type=SymbolPattern.FOREX,
                confidence=0.95,
                max_minute_lookback=timedelta(days=90),  # Forex trades 24/5
                max_daily_lookback=timedelta(days=365 * 15),
                default_interval_days=90,
                extended_hours_supported=True,  # 24-hour market
                requires_special_handling=True,
                description="Foreign exchange currency pairs",
                examples=["EUR/USD", "EURUSD", "GBP/JPY"],
            ),
            InstrumentType.OPTION: InstrumentProfile(
                instrument_type=InstrumentType.OPTION,
                pattern_type=SymbolPattern.OPTION,
                confidence=0.95,
                max_minute_lookback=timedelta(days=30),  # Options have shorter history
                max_daily_lookback=timedelta(days=365 * 2),
                default_interval_days=30,
                extended_hours_supported=False,
                requires_special_handling=True,
                api_method_override="get_option_chain",
                description="Options contracts",
                examples=["AAPL230616C00150000"],
            ),
        }

    def analyze_symbol(self, symbol: str) -> InstrumentProfile:
        """
        Analyze a symbol and return its instrument profile.

        Args:
            symbol: Trading symbol to analyze

        Returns:
            InstrumentProfile with detected type and characteristics
        """
        symbol = symbol.upper().strip()

        # Try exact matches first (highest confidence)
        # Check ETFs before indices since some symbols like SPY are in both
        if symbol in self.ETF_SYMBOLS:
            profile = self._profiles[InstrumentType.ETF]
            return InstrumentProfile(
                instrument_type=profile.instrument_type,
                pattern_type=profile.pattern_type,
                confidence=0.95,
                max_minute_lookback=profile.max_minute_lookback,
                max_daily_lookback=profile.max_daily_lookback,
                default_interval_days=profile.default_interval_days,
                extended_hours_supported=profile.extended_hours_supported,
                requires_special_handling=profile.requires_special_handling,
                description=profile.description,
                examples=profile.examples,
                api_method_override=profile.api_method_override,
            )

        if symbol in self.INDEX_SYMBOLS:
            profile = self._profiles[InstrumentType.INDEX]
            return InstrumentProfile(
                instrument_type=profile.instrument_type,
                pattern_type=profile.pattern_type,
                confidence=0.95,
                max_minute_lookback=profile.max_minute_lookback,
                max_daily_lookback=profile.max_daily_lookback,
                default_interval_days=profile.default_interval_days,
                extended_hours_supported=profile.extended_hours_supported,
                requires_special_handling=profile.requires_special_handling,
                description=profile.description,
                examples=profile.examples,
                api_method_override=profile.api_method_override,
            )

        # Pattern matching
        profile = self._analyze_by_patterns(symbol)
        if profile.confidence > 0.8:
            return profile

        # Default to equity for standard symbol format
        if self._is_likely_equity(symbol):
            base_profile = self._profiles[InstrumentType.EQUITY]
            return InstrumentProfile(
                instrument_type=base_profile.instrument_type,
                pattern_type=base_profile.pattern_type,
                confidence=0.7,  # Lower confidence for pattern-based detection
                max_minute_lookback=base_profile.max_minute_lookback,
                max_daily_lookback=base_profile.max_daily_lookback,
                default_interval_days=base_profile.default_interval_days,
                extended_hours_supported=base_profile.extended_hours_supported,
                requires_special_handling=base_profile.requires_special_handling,
                description=base_profile.description,
                examples=base_profile.examples,
                api_method_override=base_profile.api_method_override,
            )

        # Unknown symbol type
        return InstrumentProfile(
            instrument_type=InstrumentType.EQUITY,  # Default fallback
            pattern_type=SymbolPattern.UNKNOWN,
            confidence=0.3,
            max_minute_lookback=timedelta(days=48),
            max_daily_lookback=timedelta(days=365),
            default_interval_days=365,
            extended_hours_supported=True,
            requires_special_handling=False,
            description="Unknown instrument type (defaulting to equity)",
            examples=[],
        )

    def _analyze_by_patterns(self, symbol: str) -> InstrumentProfile:
        """Analyze symbol using regex patterns."""

        # Check option patterns
        for pattern in self.OPTION_PATTERNS:
            if re.match(pattern, symbol):
                return self._profiles[InstrumentType.OPTION]

        # Check futures patterns
        for pattern in self.FUTURES_PATTERNS:
            if re.match(pattern, symbol):
                return self._profiles[InstrumentType.FUTURE]

        # Check forex patterns
        for pattern in self.FOREX_PATTERNS:
            if re.match(pattern, symbol):
                return self._profiles[InstrumentType.FOREX]

        # Check crypto patterns
        for pattern in self.CRYPTO_PATTERNS:
            if re.match(pattern, symbol):
                # Create crypto profile (not in base profiles)
                return InstrumentProfile(
                    instrument_type=InstrumentType.EQUITY,  # Schwab may treat as equity
                    pattern_type=SymbolPattern.CRYPTO,
                    confidence=0.9,
                    max_minute_lookback=timedelta(days=60),
                    max_daily_lookback=timedelta(days=365 * 5),
                    default_interval_days=90,
                    extended_hours_supported=True,
                    requires_special_handling=True,
                    description="Cryptocurrency",
                    examples=["BTC-USD", "ETH-USD"],
                )

        # Check index patterns (symbols starting with $ or specific patterns)
        if symbol.startswith("$") or symbol in ["VIX", "TNX"]:
            return self._profiles[InstrumentType.INDEX]

        # No clear pattern match
        return InstrumentProfile(
            instrument_type=InstrumentType.EQUITY,
            pattern_type=SymbolPattern.UNKNOWN,
            confidence=0.4,
            max_minute_lookback=timedelta(days=48),
            max_daily_lookback=timedelta(days=365),
            default_interval_days=365,
            extended_hours_supported=True,
            requires_special_handling=False,
            description="Pattern-based analysis inconclusive",
            examples=[],
        )

    def _is_likely_equity(self, symbol: str) -> bool:
        """Determine if symbol follows common equity patterns."""
        # Simple heuristics for equity symbols
        return (
            1 <= len(symbol) <= 5  # Standard length
            and symbol.isalpha()  # Only letters
            and not symbol.startswith("$")  # Not an index
            and symbol not in self.INDEX_SYMBOLS
            and not any(
                re.match(pattern, symbol)
                for pattern in self.FUTURES_PATTERNS + self.FOREX_PATTERNS + self.OPTION_PATTERNS
            )
        )

    def get_data_limits_for_symbol(self, symbol: str) -> dict[str, timedelta]:
        """
        Get data availability limits for a specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with data availability limits
        """
        profile = self.analyze_symbol(symbol)

        return {
            "max_minute_lookback": profile.max_minute_lookback,
            "max_daily_lookback": profile.max_daily_lookback,
            "default_interval_days": timedelta(days=profile.default_interval_days),
        }

    def requires_special_api_handling(self, symbol: str) -> tuple[bool, str | None]:
        """
        Check if symbol requires special API handling.

        Args:
            symbol: Trading symbol

        Returns:
            Tuple of (requires_special_handling, api_method_override)
        """
        profile = self.analyze_symbol(symbol)
        return profile.requires_special_handling, profile.api_method_override

    def supports_extended_hours(self, symbol: str) -> bool:
        """Check if symbol supports extended hours data."""
        profile = self.analyze_symbol(symbol)
        return profile.extended_hours_supported

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """
        Get comprehensive symbol information.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with all available symbol information
        """
        profile = self.analyze_symbol(symbol)

        return {
            "symbol": symbol,
            "instrument_type": profile.instrument_type.value,
            "pattern_type": profile.pattern_type.value,
            "confidence": profile.confidence,
            "description": profile.description,
            "examples": profile.examples,
            "extended_hours_supported": profile.extended_hours_supported,
            "requires_special_handling": profile.requires_special_handling,
            "api_method_override": profile.api_method_override,
            "data_limits": {
                "max_minute_lookback_days": profile.max_minute_lookback.days,
                "max_daily_lookback_days": profile.max_daily_lookback.days,
                "default_interval_days": profile.default_interval_days,
            },
        }
