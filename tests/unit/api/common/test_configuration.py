"""
Unit tests for configuration management classes.

Tests configuration loading, validation, and environment variable integration
for all API standardization configuration classes.
"""

import pytest
from unittest.mock import patch
from pydantic import ValidationError

from src.backend.api.common.configuration import (
    APILimitsConfig,
    ValidationConfig,
    TechnicalIndicatorConfig,
    CacheConfig,
    ConfigurationManager,
    config_manager
)


class TestAPILimitsConfig:
    """Test APILimitsConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = APILimitsConfig()
        
        assert config.max_requests_per_minute == 100
        assert config.max_requests_per_hour == 1000
        assert config.max_concurrent_requests == 10
        assert config.default_page_size == 25
        assert config.max_page_size == 100
        assert config.max_page_number == 1000
        assert config.max_request_size_mb == 10.0
        assert config.max_json_depth == 10
        assert config.request_timeout_seconds == 30.0
        assert config.database_query_timeout_seconds == 15.0
        assert config.external_api_timeout_seconds == 10.0
    
    def test_environment_variable_override(self):
        """Test configuration override from environment variables."""
        with patch.dict('os.environ', {
            'TRADEASSIST_API_MAX_REQUESTS_PER_MINUTE': '200',
            'TRADEASSIST_API_DEFAULT_PAGE_SIZE': '50',
            'TRADEASSIST_API_REQUEST_TIMEOUT_SECONDS': '45.0'
        }):
            config = APILimitsConfig()
            
            assert config.max_requests_per_minute == 200
            assert config.default_page_size == 50
            assert config.request_timeout_seconds == 45.0
    
    def test_max_page_size_validation(self):
        """Test max_page_size validation."""
        # Test max_page_size too large
        with pytest.raises(ValidationError) as exc_info:
            APILimitsConfig(max_page_size=1500)
        
        assert "max_page_size cannot exceed 1000" in str(exc_info.value)
        
        # Test max_page_size less than default_page_size
        with pytest.raises(ValidationError) as exc_info:
            APILimitsConfig(default_page_size=50, max_page_size=25)
        
        assert "max_page_size must be >= default_page_size" in str(exc_info.value)
    
    def test_max_concurrent_requests_validation(self):
        """Test max_concurrent_requests validation."""
        # Test too low
        with pytest.raises(ValidationError) as exc_info:
            APILimitsConfig(max_concurrent_requests=0)
        
        assert "max_concurrent_requests must be between 1 and 100" in str(exc_info.value)
        
        # Test too high
        with pytest.raises(ValidationError) as exc_info:
            APILimitsConfig(max_concurrent_requests=150)
        
        assert "max_concurrent_requests must be between 1 and 100" in str(exc_info.value)
    
    def test_valid_configuration(self):
        """Test valid configuration creation."""
        config = APILimitsConfig(
            max_requests_per_minute=500,
            default_page_size=50,
            max_page_size=200,
            max_concurrent_requests=25
        )
        
        assert config.max_requests_per_minute == 500
        assert config.default_page_size == 50
        assert config.max_page_size == 200
        assert config.max_concurrent_requests == 25


class TestValidationConfig:
    """Test ValidationConfig class."""
    
    def test_default_values(self):
        """Test default validation configuration values."""
        config = ValidationConfig()
        
        assert config.min_lookback_hours == 1
        assert config.max_lookback_hours == 8760
        assert config.default_lookback_hours == 24
        assert config.allowed_confidence_levels == [0.90, 0.95, 0.99, 0.999]
        assert config.default_confidence_level == 0.95
        assert config.max_date_range_days == 365
        assert config.min_date_range_days == 1
        assert config.max_per_page == 100
        assert config.min_per_page == 1
        assert config.max_string_length == 1000
        assert config.max_symbol_length == 20
        assert config.max_instrument_count == 1000
        assert config.max_calculation_precision == 8
    
    def test_confidence_levels_validation(self):
        """Test confidence levels validation."""
        # Test invalid confidence level (>= 1.0)
        with pytest.raises(ValidationError) as exc_info:
            ValidationConfig(allowed_confidence_levels=[0.95, 1.0, 0.99])
        
        assert "must be between 0 and 1" in str(exc_info.value)
        
        # Test invalid confidence level (<= 0.0)
        with pytest.raises(ValidationError) as exc_info:
            ValidationConfig(allowed_confidence_levels=[0.0, 0.95, 0.99])
        
        assert "must be between 0 and 1" in str(exc_info.value)
        
        # Test valid confidence levels are sorted
        config = ValidationConfig(allowed_confidence_levels=[0.99, 0.90, 0.95])
        assert config.allowed_confidence_levels == [0.90, 0.95, 0.99]
    
    def test_default_confidence_level_validation(self):
        """Test default confidence level validation."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationConfig(
                allowed_confidence_levels=[0.90, 0.95, 0.99],
                default_confidence_level=0.85
            )
        
        assert "default_confidence_level 0.85 must be in allowed_confidence_levels" in str(exc_info.value)
    
    def test_max_lookback_hours_validation(self):
        """Test max_lookback_hours validation."""
        # Test max <= min
        with pytest.raises(ValidationError) as exc_info:
            ValidationConfig(min_lookback_hours=24, max_lookback_hours=12)
        
        assert "max_lookback_hours must be > min_lookback_hours" in str(exc_info.value)
        
        # Test unreasonably large value
        with pytest.raises(ValidationError) as exc_info:
            ValidationConfig(max_lookback_hours=100000)
        
        assert "max_lookback_hours cannot exceed 10 years" in str(exc_info.value)
    
    def test_environment_variable_override(self):
        """Test validation config override from environment variables."""
        with patch.dict('os.environ', {
            'TRADEASSIST_VALIDATION_MIN_LOOKBACK_HOURS': '2',
            'TRADEASSIST_VALIDATION_MAX_LOOKBACK_HOURS': '4380',
            'TRADEASSIST_VALIDATION_MAX_PER_PAGE': '50'
        }):
            config = ValidationConfig()
            
            assert config.min_lookback_hours == 2
            assert config.max_lookback_hours == 4380
            assert config.max_per_page == 50


class TestTechnicalIndicatorConfig:
    """Test TechnicalIndicatorConfig class."""
    
    def test_default_values(self):
        """Test default technical indicator configuration values."""
        config = TechnicalIndicatorConfig()
        
        # RSI defaults
        assert config.rsi_default_period == 14
        assert config.rsi_overbought_threshold == 70.0
        assert config.rsi_oversold_threshold == 30.0
        
        # MACD defaults
        assert config.macd_fast_period == 12
        assert config.macd_slow_period == 26
        assert config.macd_signal_period == 9
        
        # Bollinger Bands defaults
        assert config.bollinger_period == 20
        assert config.bollinger_std_dev == 2.0
        
        # Moving averages
        assert config.sma_default_periods == [10, 20, 50, 100, 200]
        assert config.ema_default_periods == [10, 20, 50, 100, 200]
        
        # Stochastic defaults
        assert config.stochastic_k_period == 14
        assert config.stochastic_d_period == 3
        assert config.stochastic_overbought == 80.0
        assert config.stochastic_oversold == 20.0
        
        # Volume and ATR
        assert config.volume_sma_period == 20
        assert config.volume_spike_threshold == 2.0
        assert config.atr_period == 14
        assert config.min_data_points == 50
    
    def test_rsi_overbought_validation(self):
        """Test RSI overbought threshold validation."""
        # Test overbought <= oversold
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicatorConfig(
                rsi_oversold_threshold=40.0,
                rsi_overbought_threshold=35.0
            )
        
        assert "rsi_overbought_threshold must be > rsi_oversold_threshold" in str(exc_info.value)
        
        # Test overbought < 50
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicatorConfig(rsi_overbought_threshold=45.0)
        
        assert "rsi_overbought_threshold must be between 50 and 100" in str(exc_info.value)
        
        # Test overbought > 100
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicatorConfig(rsi_overbought_threshold=105.0)
        
        assert "rsi_overbought_threshold must be between 50 and 100" in str(exc_info.value)
    
    def test_bollinger_std_dev_validation(self):
        """Test Bollinger Bands standard deviation validation."""
        # Test too low
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicatorConfig(bollinger_std_dev=0.3)
        
        assert "bollinger_std_dev must be between 0.5 and 3.0" in str(exc_info.value)
        
        # Test too high
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicatorConfig(bollinger_std_dev=4.0)
        
        assert "bollinger_std_dev must be between 0.5 and 3.0" in str(exc_info.value)
    
    def test_macd_periods_validation(self):
        """Test MACD periods validation."""
        with pytest.raises(ValidationError) as exc_info:
            TechnicalIndicatorConfig(
                macd_fast_period=26,
                macd_slow_period=12
            )
        
        assert "macd_slow_period must be > macd_fast_period" in str(exc_info.value)
    
    def test_environment_variable_override(self):
        """Test technical indicator config override from environment variables."""
        with patch.dict('os.environ', {
            'TRADEASSIST_INDICATOR_RSI_DEFAULT_PERIOD': '21',
            'TRADEASSIST_INDICATOR_BOLLINGER_PERIOD': '15',
            'TRADEASSIST_INDICATOR_ATR_PERIOD': '10'
        }):
            config = TechnicalIndicatorConfig()
            
            assert config.rsi_default_period == 21
            assert config.bollinger_period == 15
            assert config.atr_period == 10


class TestCacheConfig:
    """Test CacheConfig class."""
    
    def test_default_values(self):
        """Test default cache configuration values."""
        config = CacheConfig()
        
        # TTL defaults
        assert config.market_data_cache_ttl == 60
        assert config.analytics_cache_ttl == 300
        assert config.historical_data_cache_ttl == 3600
        assert config.instrument_metadata_cache_ttl == 86400
        assert config.health_status_cache_ttl == 30
        
        # Size limits
        assert config.max_cache_size_mb == 256
        assert config.max_cache_entries == 10000
        
        # Eviction policy
        assert config.cache_eviction_policy == "lru"
        assert config.cache_eviction_threshold == 0.8
        
        # Warming
        assert config.enable_cache_warming is True
        assert config.cache_warming_batch_size == 100
        
        # Redis
        assert config.redis_enabled is False
        assert config.redis_url is None
        assert config.redis_key_prefix == "tradeassist:"
        assert config.redis_connection_timeout == 5
    
    def test_eviction_policy_validation(self):
        """Test cache eviction policy validation."""
        with pytest.raises(ValidationError) as exc_info:
            CacheConfig(cache_eviction_policy="invalid_policy")
        
        assert "cache_eviction_policy must be one of:" in str(exc_info.value)
        
        # Test valid policies
        valid_policies = ["lru", "lfu", "fifo", "random"]
        for policy in valid_policies:
            config = CacheConfig(cache_eviction_policy=policy)
            assert config.cache_eviction_policy == policy
    
    def test_eviction_threshold_validation(self):
        """Test cache eviction threshold validation."""
        # Test threshold <= 0
        with pytest.raises(ValidationError) as exc_info:
            CacheConfig(cache_eviction_threshold=0.0)
        
        assert "cache_eviction_threshold must be between 0.0 and 1.0" in str(exc_info.value)
        
        # Test threshold >= 1
        with pytest.raises(ValidationError) as exc_info:
            CacheConfig(cache_eviction_threshold=1.0)
        
        assert "cache_eviction_threshold must be between 0.0 and 1.0" in str(exc_info.value)
    
    def test_max_cache_size_validation(self):
        """Test max cache size validation."""
        # Test too small
        with pytest.raises(ValidationError) as exc_info:
            CacheConfig(max_cache_size_mb=10)
        
        assert "max_cache_size_mb must be at least 16 MB" in str(exc_info.value)
        
        # Test too large
        with pytest.raises(ValidationError) as exc_info:
            CacheConfig(max_cache_size_mb=8192)
        
        assert "max_cache_size_mb cannot exceed 4096 MB" in str(exc_info.value)
    
    def test_environment_variable_override(self):
        """Test cache config override from environment variables."""
        with patch.dict('os.environ', {
            'TRADEASSIST_CACHE_MARKET_DATA_TTL': '120',
            'TRADEASSIST_CACHE_MAX_SIZE_MB': '512',
            'TRADEASSIST_CACHE_EVICTION_POLICY': 'lfu',
            'TRADEASSIST_CACHE_REDIS_ENABLED': 'true'
        }):
            config = CacheConfig()
            
            assert config.market_data_cache_ttl == 120
            assert config.max_cache_size_mb == 512
            assert config.cache_eviction_policy == "lfu"
            assert config.redis_enabled is True


class TestConfigurationManager:
    """Test ConfigurationManager class."""
    
    def test_initialization(self):
        """Test configuration manager initialization."""
        manager = ConfigurationManager()
        
        assert isinstance(manager.api_limits, APILimitsConfig)
        assert isinstance(manager.validation, ValidationConfig)
        assert isinstance(manager.indicators, TechnicalIndicatorConfig)
        assert isinstance(manager.cache, CacheConfig)
    
    def test_configuration_consistency_validation(self):
        """Test configuration consistency validation."""
        # Mock conflicting configurations
        with patch('src.backend.api.common.configuration.api_limits_config') as mock_api_limits:
            with patch('src.backend.api.common.configuration.validation_config') as mock_validation:
                mock_api_limits.max_page_size = 100
                mock_validation.max_per_page = 50
                
                with pytest.raises(ValueError) as exc_info:
                    ConfigurationManager()
                
                assert "Inconsistent pagination limits" in str(exc_info.value)
    
    def test_cache_configuration_validation(self):
        """Test cache configuration validation."""
        with patch('src.backend.api.common.configuration.cache_config') as mock_cache:
            mock_cache.max_cache_entries = 200000
            mock_cache.max_cache_size_mb = 256
            
            with pytest.raises(ValueError) as exc_info:
                ConfigurationManager()
            
            assert "Cache configuration mismatch" in str(exc_info.value)
    
    def test_get_all_settings(self):
        """Test getting all configuration settings."""
        manager = ConfigurationManager()
        settings = manager.get_all_settings()
        
        assert "api_limits" in settings
        assert "validation" in settings
        assert "indicators" in settings
        assert "cache" in settings
        
        # Test structure
        assert isinstance(settings["api_limits"], dict)
        assert "max_requests_per_minute" in settings["api_limits"]
        assert "allowed_confidence_levels" in settings["validation"]
        assert "rsi_default_period" in settings["indicators"]
        assert "market_data_cache_ttl" in settings["cache"]
    
    def test_reload_configurations(self):
        """Test configuration reloading."""
        manager = ConfigurationManager()
        original_timeout = manager.api_limits.request_timeout_seconds
        
        # Mock environment change
        with patch.dict('os.environ', {
            'TRADEASSIST_API_REQUEST_TIMEOUT_SECONDS': '60.0'
        }):
            manager.reload_configurations()
            
            # Should have new configuration
            assert manager.api_limits.request_timeout_seconds == 60.0
            assert manager.api_limits.request_timeout_seconds != original_timeout


class TestGlobalConfigurationInstances:
    """Test global configuration instances."""
    
    def test_global_config_manager_instance(self):
        """Test that global config manager instance exists and is properly initialized."""
        # Import should not raise an error
        from src.backend.api.common.configuration import config_manager
        
        assert isinstance(config_manager, ConfigurationManager)
        assert hasattr(config_manager, 'api_limits')
        assert hasattr(config_manager, 'validation')
        assert hasattr(config_manager, 'indicators')
        assert hasattr(config_manager, 'cache')
    
    def test_individual_global_configs(self):
        """Test individual global configuration instances."""
        from src.backend.api.common.configuration import (
            api_limits_config,
            validation_config,
            technical_indicator_config,
            cache_config
        )
        
        assert isinstance(api_limits_config, APILimitsConfig)
        assert isinstance(validation_config, ValidationConfig)
        assert isinstance(technical_indicator_config, TechnicalIndicatorConfig)
        assert isinstance(cache_config, CacheConfig)
    
    @patch.dict('os.environ', {
        'TRADEASSIST_API_MAX_REQUESTS_PER_MINUTE': '300',
        'TRADEASSIST_VALIDATION_MAX_PER_PAGE': '150'
    })
    def test_environment_integration(self):
        """Test that global instances properly integrate with environment."""
        # Force reload by creating new instances
        config = APILimitsConfig()
        validation = ValidationConfig()
        
        assert config.max_requests_per_minute == 300
        assert validation.max_per_page == 150
    
    def test_configuration_immutability_patterns(self):
        """Test that configurations behave properly as shared instances."""
        from src.backend.api.common.configuration import api_limits_config
        
        # Multiple imports should give same instance
        from src.backend.api.common.configuration import api_limits_config as config2
        
        assert api_limits_config is config2
        
        # Configuration should be consistent
        assert api_limits_config.max_requests_per_minute == config2.max_requests_per_minute