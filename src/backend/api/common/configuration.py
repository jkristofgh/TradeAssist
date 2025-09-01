"""
Centralized configuration management for API standardization.

This module provides configuration classes that replace hardcoded values
throughout the codebase with environment-configurable settings.
"""

from typing import List, Dict, Any, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class APILimitsConfig(BaseSettings):
    """
    Configuration for API rate limiting, pagination, and request constraints.
    
    Centralizes hardcoded limits and provides environment-based configuration
    for API behavior tuning.
    """
    
    # Rate limiting configuration
    max_requests_per_minute: int = Field(
        default=100,
        description="Maximum requests per minute per client",
        env="API_MAX_REQUESTS_PER_MINUTE"
    )
    
    max_requests_per_hour: int = Field(
        default=1000,
        description="Maximum requests per hour per client",
        env="API_MAX_REQUESTS_PER_HOUR"
    )
    
    max_concurrent_requests: int = Field(
        default=10,
        description="Maximum concurrent requests per client",
        env="API_MAX_CONCURRENT_REQUESTS"
    )
    
    # Pagination limits
    default_page_size: int = Field(
        default=25,
        description="Default number of items per page",
        env="API_DEFAULT_PAGE_SIZE"
    )
    
    max_page_size: int = Field(
        default=100,
        description="Maximum number of items per page",
        env="API_MAX_PAGE_SIZE"
    )
    
    max_page_number: int = Field(
        default=1000,
        description="Maximum page number allowed",
        env="API_MAX_PAGE_NUMBER"
    )
    
    # Request size limits
    max_request_size_mb: float = Field(
        default=10.0,
        description="Maximum request size in megabytes",
        env="API_MAX_REQUEST_SIZE_MB"
    )
    
    max_json_depth: int = Field(
        default=10,
        description="Maximum JSON nesting depth",
        env="API_MAX_JSON_DEPTH"
    )
    
    # Timeout configuration
    request_timeout_seconds: float = Field(
        default=30.0,
        description="Request timeout in seconds",
        env="API_REQUEST_TIMEOUT_SECONDS"
    )
    
    database_query_timeout_seconds: float = Field(
        default=15.0,
        description="Database query timeout in seconds",
        env="API_DATABASE_QUERY_TIMEOUT_SECONDS"
    )
    
    external_api_timeout_seconds: float = Field(
        default=10.0,
        description="External API call timeout in seconds",
        env="API_EXTERNAL_API_TIMEOUT_SECONDS"
    )
    
    @validator("max_page_size")
    def validate_max_page_size(cls, v, values):
        """Ensure max_page_size is reasonable."""
        if v > 1000:
            raise ValueError("max_page_size cannot exceed 1000")
        default_size = values.get("default_page_size", 25)
        if v < default_size:
            raise ValueError("max_page_size must be >= default_page_size")
        return v
    
    @validator("max_concurrent_requests")
    def validate_max_concurrent_requests(cls, v):
        """Ensure max_concurrent_requests is reasonable."""
        if v < 1 or v > 100:
            raise ValueError("max_concurrent_requests must be between 1 and 100")
        return v
    
    class Config:
        env_prefix = "TRADEASSIST_"
        case_sensitive = False


class ValidationConfig(BaseSettings):
    """
    Configuration for parameter validation rules and constraints.
    
    Centralizes validation thresholds and provides environment-based
    configuration for validation behavior.
    """
    
    # Lookback time limits
    min_lookback_hours: int = Field(
        default=1,
        description="Minimum lookback hours for analytics queries",
        env="VALIDATION_MIN_LOOKBACK_HOURS"
    )
    
    max_lookback_hours: int = Field(
        default=8760,  # 1 year
        description="Maximum lookback hours for analytics queries",
        env="VALIDATION_MAX_LOOKBACK_HOURS"
    )
    
    default_lookback_hours: int = Field(
        default=24,
        description="Default lookback hours when not specified",
        env="VALIDATION_DEFAULT_LOOKBACK_HOURS"
    )
    
    # Confidence level validation
    allowed_confidence_levels: List[float] = Field(
        default=[0.90, 0.95, 0.99, 0.999],
        description="Allowed confidence levels for ML predictions",
        env="VALIDATION_ALLOWED_CONFIDENCE_LEVELS"
    )
    
    default_confidence_level: float = Field(
        default=0.95,
        description="Default confidence level when not specified",
        env="VALIDATION_DEFAULT_CONFIDENCE_LEVEL"
    )
    
    # Date range validation
    max_date_range_days: int = Field(
        default=365,
        description="Maximum date range in days for historical queries",
        env="VALIDATION_MAX_DATE_RANGE_DAYS"
    )
    
    min_date_range_days: int = Field(
        default=1,
        description="Minimum date range in days for historical queries",
        env="VALIDATION_MIN_DATE_RANGE_DAYS"
    )
    
    # Pagination validation
    max_per_page: int = Field(
        default=100,
        description="Maximum items per page for list endpoints",
        env="VALIDATION_MAX_PER_PAGE"
    )
    
    min_per_page: int = Field(
        default=1,
        description="Minimum items per page for list endpoints",
        env="VALIDATION_MIN_PER_PAGE"
    )
    
    # String validation
    max_string_length: int = Field(
        default=1000,
        description="Maximum length for string parameters",
        env="VALIDATION_MAX_STRING_LENGTH"
    )
    
    max_symbol_length: int = Field(
        default=20,
        description="Maximum length for instrument symbols",
        env="VALIDATION_MAX_SYMBOL_LENGTH"
    )
    
    # Numeric validation
    max_instrument_count: int = Field(
        default=1000,
        description="Maximum number of instruments in batch operations",
        env="VALIDATION_MAX_INSTRUMENT_COUNT"
    )
    
    max_calculation_precision: int = Field(
        default=8,
        description="Maximum decimal precision for calculations",
        env="VALIDATION_MAX_CALCULATION_PRECISION"
    )
    
    @validator("allowed_confidence_levels")
    def validate_confidence_levels(cls, v):
        """Ensure confidence levels are valid."""
        for level in v:
            if not (0.0 < level < 1.0):
                raise ValueError(f"Confidence level {level} must be between 0 and 1")
        return sorted(v)  # Keep sorted for consistency
    
    @validator("default_confidence_level")
    def validate_default_confidence_level(cls, v, values):
        """Ensure default confidence level is in allowed list."""
        allowed = values.get("allowed_confidence_levels", [0.90, 0.95, 0.99, 0.999])
        if v not in allowed:
            raise ValueError(f"default_confidence_level {v} must be in allowed_confidence_levels {allowed}")
        return v
    
    @validator("max_lookback_hours")
    def validate_max_lookback_hours(cls, v, values):
        """Ensure max_lookback_hours is reasonable."""
        min_hours = values.get("min_lookback_hours", 1)
        if v <= min_hours:
            raise ValueError("max_lookback_hours must be > min_lookback_hours")
        if v > 87600:  # 10 years
            raise ValueError("max_lookback_hours cannot exceed 10 years (87600 hours)")
        return v
    
    class Config:
        env_prefix = "TRADEASSIST_"
        case_sensitive = False


class TechnicalIndicatorConfig(BaseSettings):
    """
    Configuration for technical indicator calculations and parameters.
    
    Centralizes technical analysis parameters and provides environment-based
    configuration for indicator calculations.
    """
    
    # RSI (Relative Strength Index) configuration
    rsi_default_period: int = Field(
        default=14,
        description="Default RSI calculation period",
        env="INDICATOR_RSI_DEFAULT_PERIOD"
    )
    
    rsi_overbought_threshold: float = Field(
        default=70.0,
        description="RSI overbought threshold",
        env="INDICATOR_RSI_OVERBOUGHT_THRESHOLD"
    )
    
    rsi_oversold_threshold: float = Field(
        default=30.0,
        description="RSI oversold threshold",
        env="INDICATOR_RSI_OVERSOLD_THRESHOLD"
    )
    
    # MACD (Moving Average Convergence Divergence) configuration
    macd_fast_period: int = Field(
        default=12,
        description="MACD fast EMA period",
        env="INDICATOR_MACD_FAST_PERIOD"
    )
    
    macd_slow_period: int = Field(
        default=26,
        description="MACD slow EMA period",
        env="INDICATOR_MACD_SLOW_PERIOD"
    )
    
    macd_signal_period: int = Field(
        default=9,
        description="MACD signal line EMA period",
        env="INDICATOR_MACD_SIGNAL_PERIOD"
    )
    
    # Bollinger Bands configuration
    bollinger_period: int = Field(
        default=20,
        description="Bollinger Bands moving average period",
        env="INDICATOR_BOLLINGER_PERIOD"
    )
    
    bollinger_std_dev: float = Field(
        default=2.0,
        description="Bollinger Bands standard deviation multiplier",
        env="INDICATOR_BOLLINGER_STD_DEV"
    )
    
    # Moving Average configuration
    sma_default_periods: List[int] = Field(
        default=[10, 20, 50, 100, 200],
        description="Default SMA periods for analysis",
        env="INDICATOR_SMA_DEFAULT_PERIODS"
    )
    
    ema_default_periods: List[int] = Field(
        default=[10, 20, 50, 100, 200],
        description="Default EMA periods for analysis",
        env="INDICATOR_EMA_DEFAULT_PERIODS"
    )
    
    # Stochastic Oscillator configuration
    stochastic_k_period: int = Field(
        default=14,
        description="Stochastic %K period",
        env="INDICATOR_STOCHASTIC_K_PERIOD"
    )
    
    stochastic_d_period: int = Field(
        default=3,
        description="Stochastic %D smoothing period",
        env="INDICATOR_STOCHASTIC_D_PERIOD"
    )
    
    stochastic_overbought: float = Field(
        default=80.0,
        description="Stochastic overbought threshold",
        env="INDICATOR_STOCHASTIC_OVERBOUGHT"
    )
    
    stochastic_oversold: float = Field(
        default=20.0,
        description="Stochastic oversold threshold",
        env="INDICATOR_STOCHASTIC_OVERSOLD"
    )
    
    # Volume indicators
    volume_sma_period: int = Field(
        default=20,
        description="Volume SMA period for volume analysis",
        env="INDICATOR_VOLUME_SMA_PERIOD"
    )
    
    volume_spike_threshold: float = Field(
        default=2.0,
        description="Volume spike threshold (multiples of average)",
        env="INDICATOR_VOLUME_SPIKE_THRESHOLD"
    )
    
    # ATR (Average True Range) configuration
    atr_period: int = Field(
        default=14,
        description="ATR calculation period",
        env="INDICATOR_ATR_PERIOD"
    )
    
    # Minimum data requirements
    min_data_points: int = Field(
        default=50,
        description="Minimum data points required for reliable calculations",
        env="INDICATOR_MIN_DATA_POINTS"
    )
    
    @validator("rsi_overbought_threshold")
    def validate_rsi_overbought(cls, v, values):
        """Ensure RSI overbought threshold is valid."""
        oversold = values.get("rsi_oversold_threshold", 30.0)
        if v <= oversold:
            raise ValueError("rsi_overbought_threshold must be > rsi_oversold_threshold")
        if not (50.0 <= v <= 100.0):
            raise ValueError("rsi_overbought_threshold must be between 50 and 100")
        return v
    
    @validator("bollinger_std_dev")
    def validate_bollinger_std_dev(cls, v):
        """Ensure Bollinger Bands standard deviation is reasonable."""
        if not (0.5 <= v <= 3.0):
            raise ValueError("bollinger_std_dev must be between 0.5 and 3.0")
        return v
    
    @validator("macd_slow_period")
    def validate_macd_periods(cls, v, values):
        """Ensure MACD slow period > fast period."""
        fast_period = values.get("macd_fast_period", 12)
        if v <= fast_period:
            raise ValueError("macd_slow_period must be > macd_fast_period")
        return v
    
    class Config:
        env_prefix = "TRADEASSIST_"
        case_sensitive = False


class CacheConfig(BaseSettings):
    """
    Configuration for caching strategies and cache management.
    
    Centralizes cache settings and provides environment-based configuration
    for cache behavior tuning.
    """
    
    # Cache TTL (Time To Live) configuration in seconds
    market_data_cache_ttl: int = Field(
        default=60,  # 1 minute
        description="Market data cache TTL in seconds",
        env="CACHE_MARKET_DATA_TTL"
    )
    
    analytics_cache_ttl: int = Field(
        default=300,  # 5 minutes
        description="Analytics results cache TTL in seconds",
        env="CACHE_ANALYTICS_TTL"
    )
    
    historical_data_cache_ttl: int = Field(
        default=3600,  # 1 hour
        description="Historical data cache TTL in seconds",
        env="CACHE_HISTORICAL_DATA_TTL"
    )
    
    instrument_metadata_cache_ttl: int = Field(
        default=86400,  # 24 hours
        description="Instrument metadata cache TTL in seconds",
        env="CACHE_INSTRUMENT_METADATA_TTL"
    )
    
    health_status_cache_ttl: int = Field(
        default=30,  # 30 seconds
        description="Health status cache TTL in seconds",
        env="CACHE_HEALTH_STATUS_TTL"
    )
    
    # Cache size limits
    max_cache_size_mb: int = Field(
        default=256,
        description="Maximum cache size in megabytes",
        env="CACHE_MAX_SIZE_MB"
    )
    
    max_cache_entries: int = Field(
        default=10000,
        description="Maximum number of cache entries",
        env="CACHE_MAX_ENTRIES"
    )
    
    # Cache eviction policy
    cache_eviction_policy: str = Field(
        default="lru",
        description="Cache eviction policy (lru, lfu, fifo)",
        env="CACHE_EVICTION_POLICY"
    )
    
    cache_eviction_threshold: float = Field(
        default=0.8,
        description="Cache size threshold for eviction (0.0-1.0)",
        env="CACHE_EVICTION_THRESHOLD"
    )
    
    # Cache warming configuration
    enable_cache_warming: bool = Field(
        default=True,
        description="Enable cache warming on startup",
        env="CACHE_ENABLE_WARMING"
    )
    
    cache_warming_batch_size: int = Field(
        default=100,
        description="Batch size for cache warming operations",
        env="CACHE_WARMING_BATCH_SIZE"
    )
    
    # Redis configuration (if using Redis cache)
    redis_enabled: bool = Field(
        default=False,
        description="Enable Redis caching",
        env="CACHE_REDIS_ENABLED"
    )
    
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL",
        env="CACHE_REDIS_URL"
    )
    
    redis_key_prefix: str = Field(
        default="tradeassist:",
        description="Redis key prefix",
        env="CACHE_REDIS_KEY_PREFIX"
    )
    
    redis_connection_timeout: int = Field(
        default=5,
        description="Redis connection timeout in seconds",
        env="CACHE_REDIS_CONNECTION_TIMEOUT"
    )
    
    @validator("cache_eviction_policy")
    def validate_eviction_policy(cls, v):
        """Ensure cache eviction policy is valid."""
        allowed_policies = ["lru", "lfu", "fifo", "random"]
        if v not in allowed_policies:
            raise ValueError(f"cache_eviction_policy must be one of: {allowed_policies}")
        return v
    
    @validator("cache_eviction_threshold")
    def validate_eviction_threshold(cls, v):
        """Ensure cache eviction threshold is valid."""
        if not (0.0 < v < 1.0):
            raise ValueError("cache_eviction_threshold must be between 0.0 and 1.0")
        return v
    
    @validator("max_cache_size_mb")
    def validate_max_cache_size(cls, v):
        """Ensure max cache size is reasonable."""
        if v < 16:  # Minimum 16MB
            raise ValueError("max_cache_size_mb must be at least 16 MB")
        if v > 4096:  # Maximum 4GB
            raise ValueError("max_cache_size_mb cannot exceed 4096 MB")
        return v
    
    class Config:
        env_prefix = "TRADEASSIST_"
        case_sensitive = False


# Global configuration instances
api_limits_config = APILimitsConfig()
validation_config = ValidationConfig()
technical_indicator_config = TechnicalIndicatorConfig()
cache_config = CacheConfig()


class ConfigurationManager:
    """
    Centralized configuration manager for all API standardization settings.
    
    Provides unified access to all configuration classes and validation
    of cross-configuration dependencies.
    """
    
    def __init__(self):
        """Initialize configuration manager with all config instances."""
        self.api_limits = api_limits_config
        self.validation = validation_config
        self.indicators = technical_indicator_config
        self.cache = cache_config
        
        # Validate cross-configuration dependencies
        self._validate_configurations()
    
    def _validate_configurations(self):
        """Validate configuration consistency across modules."""
        # Ensure pagination limits are consistent
        if self.api_limits.max_page_size != self.validation.max_per_page:
            raise ValueError(
                "Inconsistent pagination limits: "
                f"api_limits.max_page_size ({self.api_limits.max_page_size}) != "
                f"validation.max_per_page ({self.validation.max_per_page})"
            )
        
        # Ensure cache sizes are reasonable for expected load
        if self.cache.max_cache_entries > 100000 and self.cache.max_cache_size_mb < 512:
            raise ValueError(
                "Cache configuration mismatch: high entry count requires more memory"
            )
    
    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all configuration settings as a dictionary.
        
        Returns:
            Dict containing all configuration values
        """
        return {
            "api_limits": self.api_limits.dict(),
            "validation": self.validation.dict(),
            "indicators": self.indicators.dict(),
            "cache": self.cache.dict()
        }
    
    def reload_configurations(self):
        """Reload all configurations from environment variables."""
        self.api_limits = APILimitsConfig()
        self.validation = ValidationConfig()
        self.indicators = TechnicalIndicatorConfig()
        self.cache = CacheConfig()
        self._validate_configurations()


# Global configuration manager instance
config_manager = ConfigurationManager()