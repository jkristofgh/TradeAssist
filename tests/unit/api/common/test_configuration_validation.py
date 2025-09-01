"""
Unit tests for Configuration Validation API - Phase 3.

Tests the runtime configuration validation endpoints and
configuration management functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from src.backend.api.common.configuration import (
    APILimitsConfig,
    ValidationConfig, 
    TechnicalIndicatorConfig,
    CacheConfig,
    MonitoringConfig,
    ConfigurationManager
)


class TestMonitoringConfig:
    """Test the MonitoringConfig class."""
    
    def test_monitoring_config_defaults(self):
        """Test MonitoringConfig default values."""
        config = MonitoringConfig()
        
        assert config.enable_error_tracking is True
        assert config.error_sample_rate == 1.0
        assert config.max_error_details_length == 1000
        assert config.enable_performance_tracking is True
        assert config.performance_sample_rate == 1.0
        assert config.slow_query_threshold_ms == 1000.0
        assert config.slow_request_threshold_ms == 2000.0
        assert config.enable_alerting is False
        assert config.error_rate_alert_threshold == 0.05
        assert config.response_time_alert_threshold_ms == 5000.0
        assert config.alert_cooldown_minutes == 15
    
    def test_monitoring_config_validation(self):
        """Test MonitoringConfig validation rules."""
        # Test valid configuration
        config = MonitoringConfig(
            error_sample_rate=0.5,
            performance_sample_rate=0.8,
            cpu_usage_alert_threshold_percent=75.0,
            metrics_retention_days=15
        )
        
        assert config.error_sample_rate == 0.5
        assert config.cpu_usage_alert_threshold_percent == 75.0
        assert config.metrics_retention_days == 15
    
    def test_monitoring_config_invalid_rates(self):
        """Test MonitoringConfig with invalid rate values."""
        with pytest.raises(ValueError, match="Rate values must be between 0.0 and 1.0"):
            MonitoringConfig(error_sample_rate=1.5)
        
        with pytest.raises(ValueError, match="Rate values must be between 0.0 and 1.0"):
            MonitoringConfig(performance_sample_rate=-0.1)
        
        with pytest.raises(ValueError, match="Rate values must be between 0.0 and 1.0"):
            MonitoringConfig(error_rate_alert_threshold=2.0)
    
    def test_monitoring_config_invalid_cpu_threshold(self):
        """Test MonitoringConfig with invalid CPU threshold."""
        with pytest.raises(ValueError, match="CPU usage threshold must be between 0.0 and 100.0"):
            MonitoringConfig(cpu_usage_alert_threshold_percent=150.0)
        
        with pytest.raises(ValueError, match="CPU usage threshold must be between 0.0 and 100.0"):
            MonitoringConfig(cpu_usage_alert_threshold_percent=-10.0)
    
    def test_monitoring_config_invalid_retention_days(self):
        """Test MonitoringConfig with invalid retention days."""
        with pytest.raises(ValueError, match="Retention days must be at least 1"):
            MonitoringConfig(metrics_retention_days=0)
        
        with pytest.raises(ValueError, match="Retention days cannot exceed 365"):
            MonitoringConfig(config_change_retention_days=400)


class TestConfigurationManager:
    """Test the ConfigurationManager class."""
    
    def test_configuration_manager_initialization(self):
        """Test ConfigurationManager initialization."""
        manager = ConfigurationManager()
        
        assert hasattr(manager, 'api_limits')
        assert hasattr(manager, 'validation')
        assert hasattr(manager, 'indicators')
        assert hasattr(manager, 'cache')
        assert hasattr(manager, 'monitoring')
        
        assert isinstance(manager.api_limits, APILimitsConfig)
        assert isinstance(manager.validation, ValidationConfig)
        assert isinstance(manager.indicators, TechnicalIndicatorConfig)
        assert isinstance(manager.cache, CacheConfig)
        assert isinstance(manager.monitoring, MonitoringConfig)
    
    def test_get_all_settings(self):
        """Test getting all configuration settings."""
        manager = ConfigurationManager()
        
        all_settings = manager.get_all_settings()
        
        assert "api_limits" in all_settings
        assert "validation" in all_settings
        assert "indicators" in all_settings
        assert "cache" in all_settings
        assert "monitoring" in all_settings
        
        # Check that settings contain expected keys
        assert "max_page_size" in all_settings["api_limits"]
        assert "max_lookback_hours" in all_settings["validation"]
        assert "rsi_default_period" in all_settings["indicators"]
        assert "market_data_cache_ttl" in all_settings["cache"]
        assert "enable_error_tracking" in all_settings["monitoring"]
    
    def test_reload_configurations(self):
        """Test reloading configurations."""
        manager = ConfigurationManager()
        
        # Store original values
        original_page_size = manager.api_limits.max_page_size
        
        # Reload configurations (should create new instances)
        manager.reload_configurations()
        
        # Should still have same values (no env changes)
        assert manager.api_limits.max_page_size == original_page_size
        
        # But should be new instances
        assert hasattr(manager, 'api_limits')
        assert isinstance(manager.api_limits, APILimitsConfig)
    
    def test_configuration_consistency_validation(self):
        """Test cross-configuration validation."""
        # This should work - consistent pagination limits
        manager = ConfigurationManager()
        
        # Modify to create inconsistency
        manager.api_limits.max_page_size = 50
        manager.validation.max_per_page = 100
        
        # Should raise validation error on next validation
        with pytest.raises(ValueError, match="Inconsistent pagination limits"):
            manager._validate_configurations()


@pytest.mark.asyncio
class TestConfigurationValidationEndpoints:
    """Test configuration validation API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.backend.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_validate_configuration_success(self, client):
        """Test successful configuration validation."""
        with patch('src.backend.api.common.configuration.config_manager') as mock_manager:
            # Setup mock configuration
            mock_config = MagicMock()
            mock_config.dict.return_value = {"test": "value"}
            
            mock_manager.api_limits = mock_config
            mock_manager.validation = mock_config
            mock_manager.indicators = mock_config
            mock_manager.cache = mock_config
            mock_manager.monitoring = mock_config
            
            response = client.get("/api/health/config/validate")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "validation_summary" in data
            assert "section_details" in data
            assert data["validation_summary"]["total_sections"] == 5
    
    def test_validate_configuration_specific_section(self, client):
        """Test validating specific configuration section."""
        with patch('src.backend.api.common.configuration.config_manager') as mock_manager:
            # Setup mock configuration
            mock_config = MagicMock()
            mock_config.dict.return_value = {"test": "value"}
            mock_manager.api_limits = mock_config
            
            response = client.get("/api/health/config/validate?config_section=api_limits")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "api_limits" in data["section_details"]
            assert len(data["section_details"]) == 1
    
    def test_validate_configuration_invalid_section(self, client):
        """Test validating invalid configuration section."""
        response = client.get("/api/health/config/validate?config_section=invalid")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert "Invalid configuration section" in data["error"]
        assert "valid_sections" in data
    
    def test_get_current_configuration(self, client):
        """Test getting current configuration."""
        with patch('src.backend.api.common.configuration.config_manager') as mock_manager:
            mock_settings = {
                "api_limits": {"max_page_size": 100},
                "validation": {"max_lookback_hours": 8760},
                "indicators": {"rsi_default_period": 14},
                "cache": {"market_data_cache_ttl": 60},
                "monitoring": {"enable_error_tracking": True}
            }
            mock_manager.get_all_settings.return_value = mock_settings
            
            response = client.get("/api/health/config/current")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "configuration" in data
            assert data["configuration"] == mock_settings
            assert data["metadata"]["sections_included"] == 5
            assert data["metadata"]["sensitive_data_included"] is False
    
    def test_get_current_configuration_with_sensitive(self, client):
        """Test getting configuration with sensitive data."""
        with patch('src.backend.api.common.configuration.config_manager') as mock_manager:
            mock_settings = {
                "monitoring": {
                    "external_monitoring_api_key": "secret123",
                    "external_monitoring_endpoint": "https://example.com/api"
                }
            }
            mock_manager.get_all_settings.return_value = mock_settings
            
            response = client.get("/api/health/config/current?include_sensitive=false")
            
            assert response.status_code == 200
            data = response.json()
            
            # Sensitive data should be redacted
            monitoring_config = data["configuration"]["monitoring"]
            assert monitoring_config["external_monitoring_api_key"] == "***REDACTED***"
            assert monitoring_config["external_monitoring_endpoint"] == "***REDACTED***"
    
    def test_get_current_configuration_specific_section(self, client):
        """Test getting specific configuration section."""
        with patch('src.backend.api.common.configuration.config_manager') as mock_manager:
            mock_settings = {
                "api_limits": {"max_page_size": 100},
                "validation": {"max_lookback_hours": 8760}
            }
            mock_manager.get_all_settings.return_value = mock_settings
            
            response = client.get("/api/health/config/current?config_section=api_limits")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "configuration" in data
            assert "api_limits" in data["configuration"]
            assert len(data["configuration"]) == 1
    
    def test_reload_configuration(self, client):
        """Test reloading configuration."""
        with patch('src.backend.api.common.configuration.config_manager') as mock_manager:
            # Mock previous and new configurations
            previous_config = {"api_limits": {"max_page_size": 100}}
            new_config = {"api_limits": {"max_page_size": 150}}
            
            mock_manager.get_all_settings.side_effect = [previous_config, new_config]
            mock_manager.reload_configurations.return_value = None
            
            response = client.post("/api/health/config/reload")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "reload_summary" in data
            assert "configuration_changes" in data
            assert data["reload_summary"]["sections_reloaded"] == 1
            assert data["reload_summary"]["changes_detected"] == 1
            
            # Check that reload_configurations was called
            mock_manager.reload_configurations.assert_called_once()
    
    def test_configuration_validation_error_handling(self, client):
        """Test error handling in configuration validation."""
        with patch('src.backend.api.common.configuration.config_manager') as mock_manager:
            # Make config_manager raise an exception
            mock_manager.api_limits = MagicMock()
            mock_manager.api_limits.dict.side_effect = Exception("Test error")
            
            response = client.get("/api/health/config/validate")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is False
            assert "Configuration validation failed" in data["error"]


@pytest.mark.integration 
class TestConfigurationIntegration:
    """Integration tests for configuration management."""
    
    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        import os
        
        # Set environment variable
        os.environ["TRADEASSIST_API_MAX_PAGE_SIZE"] = "75"
        
        try:
            # Create new config instance
            config = APILimitsConfig()
            
            assert config.max_page_size == 75
            
        finally:
            # Clean up environment variable
            if "TRADEASSIST_API_MAX_PAGE_SIZE" in os.environ:
                del os.environ["TRADEASSIST_API_MAX_PAGE_SIZE"]
    
    def test_configuration_manager_integration(self):
        """Test ConfigurationManager with all config classes."""
        manager = ConfigurationManager()
        
        # Test that all configurations are accessible
        assert manager.api_limits.max_page_size > 0
        assert manager.validation.max_lookback_hours > 0
        assert manager.indicators.rsi_default_period > 0
        assert manager.cache.market_data_cache_ttl > 0
        assert manager.monitoring.slow_request_threshold_ms > 0
        
        # Test getting all settings
        all_settings = manager.get_all_settings()
        assert len(all_settings) == 5
        
        # Test that each section has expected structure
        for section_name, section_data in all_settings.items():
            assert isinstance(section_data, dict)
            assert len(section_data) > 0


if __name__ == "__main__":
    pytest.main([__file__])