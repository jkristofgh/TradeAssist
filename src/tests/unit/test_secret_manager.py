"""
Unit tests for Google Cloud Secret Manager service.
"""

import asyncio
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from src.backend.services.secret_manager import (
    GoogleCloudSecretManager,
    LocalSecretCache,
    SecretMetadata
)


class TestLocalSecretCache:
    """Test cases for LocalSecretCache."""
    
    def setup_method(self):
        """Setup test cache with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = LocalSecretCache(self.temp_dir)
    
    def test_cache_initialization(self):
        """Test cache initialization creates encryption key."""
        assert self.cache.cache_dir.exists()
        key_file = self.cache.cache_dir / "cache.key"
        assert key_file.exists()
        assert self.cache.fernet is not None
    
    def test_cache_set_and_get(self):
        """Test setting and getting cached data."""
        test_data = {"username": "test", "password": "secret"}
        
        # Set cache entry
        self.cache.set("test-secret", test_data, ttl=3600)
        
        # Get cache entry
        retrieved_data = self.cache.get("test-secret")
        assert retrieved_data == test_data
    
    def test_cache_expiration(self):
        """Test cache entry expiration."""
        test_data = {"value": "test"}
        
        # Set with very short TTL
        self.cache.set("test-secret", test_data, ttl=0)
        
        # Should be expired immediately
        retrieved_data = self.cache.get("test-secret")
        assert retrieved_data is None
    
    def test_cache_invalidation(self):
        """Test cache entry invalidation."""
        test_data = {"value": "test"}
        
        # Set and verify cache
        self.cache.set("test-secret", test_data)
        assert self.cache.get("test-secret") == test_data
        
        # Invalidate and verify removal
        self.cache.invalidate("test-secret")
        assert self.cache.get("test-secret") is None
    
    def test_clear_expired(self):
        """Test clearing expired entries."""
        # Set some entries with different TTLs
        self.cache.set("valid", {"value": "valid"}, ttl=3600)
        self.cache.set("expired1", {"value": "expired1"}, ttl=0)
        self.cache.set("expired2", {"value": "expired2"}, ttl=0)
        
        # Clear expired entries
        cleared_count = self.cache.clear_expired()
        
        # Should have cleared 2 expired entries
        assert cleared_count == 2
        
        # Valid entry should still exist
        assert self.cache.get("valid") == {"value": "valid"}


class TestGoogleCloudSecretManager:
    """Test cases for GoogleCloudSecretManager."""
    
    def setup_method(self):
        """Setup test secret manager."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            self.secret_manager = GoogleCloudSecretManager()
    
    @patch('src.backend.services.secret_manager.secretmanager.SecretManagerServiceClient')
    def test_initialization_with_credentials(self, mock_client_class):
        """Test initialization with valid credentials."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            sm = GoogleCloudSecretManager()
            assert sm.enabled is True
            assert sm.client is not None
    
    def test_initialization_without_credentials(self):
        """Test initialization without credentials."""
        with patch.dict('os.environ', {}, clear=True):
            sm = GoogleCloudSecretManager()
            assert sm.enabled is False
            assert sm.client is None
    
    @pytest.mark.asyncio
    async def test_get_secret_from_cache(self):
        """Test getting secret from cache."""
        # Mock cache to return value
        self.secret_manager.cache.get = Mock(return_value={"value": "cached-secret"})
        
        result = await self.secret_manager.get_secret("test-secret")
        assert result == "cached-secret"
    
    @pytest.mark.asyncio
    async def test_get_secret_fallback_to_env(self):
        """Test fallback to environment variable."""
        # Mock cache miss and GCP failure
        self.secret_manager.cache.get = Mock(return_value=None)
        self.secret_manager.enabled = False
        
        with patch.dict('os.environ', {'TEST_SECRET': 'env-secret'}):
            result = await self.secret_manager.get_secret(
                "test-secret", 
                fallback_env_var="TEST_SECRET"
            )
            assert result == "env-secret"
    
    @pytest.mark.asyncio
    @patch('src.backend.services.secret_manager.secretmanager.SecretManagerServiceClient')
    async def test_get_secret_from_gcp(self, mock_client_class):
        """Test getting secret from Google Cloud."""
        # Setup mock client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.payload.data.decode.return_value = "gcp-secret"
        mock_client.access_secret_version.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Setup secret manager
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            sm = GoogleCloudSecretManager()
            sm.cache.get = Mock(return_value=None)  # Cache miss
            
            result = await sm.get_secret("test-secret")
            assert result == "gcp-secret"
            
            # Verify client was called correctly
            mock_client.access_secret_version.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.backend.services.secret_manager.secretmanager.SecretManagerServiceClient')
    async def test_create_secret(self, mock_client_class):
        """Test creating a new secret."""
        mock_client = Mock()
        mock_secret = Mock()
        mock_secret.name = "projects/test/secrets/test-secret"
        mock_client.create_secret.return_value = mock_secret
        mock_version = Mock()
        mock_client.add_secret_version.return_value = mock_version
        mock_client_class.return_value = mock_client
        
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            sm = GoogleCloudSecretManager()
            
            result = await sm.create_secret("test-secret", "secret-value")
            assert result is True
            
            # Verify calls
            mock_client.create_secret.assert_called_once()
            mock_client.add_secret_version.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.backend.services.secret_manager.secretmanager.SecretManagerServiceClient')
    async def test_update_secret(self, mock_client_class):
        """Test updating an existing secret."""
        mock_client = Mock()
        mock_version = Mock()
        mock_client.add_secret_version.return_value = mock_version
        mock_client_class.return_value = mock_client
        
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            sm = GoogleCloudSecretManager()
            sm.cache = Mock()
            
            result = await sm.update_secret("test-secret", "new-value")
            assert result is True
            
            # Verify cache invalidation
            sm.cache.invalidate.assert_called_once_with("test-secret:latest")
    
    @pytest.mark.asyncio
    @patch('src.backend.services.secret_manager.secretmanager.SecretManagerServiceClient')
    async def test_list_secrets(self, mock_client_class):
        """Test listing all secrets."""
        mock_client = Mock()
        
        # Mock secret objects
        mock_secret = Mock()
        mock_secret.name = "projects/test/secrets/test-secret"
        mock_secret.create_time.timestamp.return_value = 1640995200  # Jan 1, 2022
        mock_secret.labels = {}
        
        mock_version = Mock()
        mock_version.name = "projects/test/secrets/test-secret/versions/1"
        
        mock_client.list_secrets.return_value = [mock_secret]
        mock_client.list_secret_versions.return_value = [mock_version]
        mock_client_class.return_value = mock_client
        
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            sm = GoogleCloudSecretManager()
            
            secrets = await sm.list_secrets()
            assert len(secrets) == 1
            assert isinstance(secrets[0], SecretMetadata)
            assert secrets[0].name == "test-secret"
    
    @pytest.mark.asyncio
    async def test_get_schwab_credentials(self):
        """Test getting Schwab API credentials."""
        # Mock the get_secret method
        async def mock_get_secret(secret_name, fallback_env_var=None):
            if secret_name == "schwab-app-key":
                return "test-app-key"
            elif secret_name == "schwab-app-secret":
                return "test-app-secret"
            return None
        
        self.secret_manager.get_secret = mock_get_secret
        
        credentials = await self.secret_manager.get_schwab_credentials()
        
        assert credentials == {
            "app_key": "test-app-key",
            "app_secret": "test-app-secret"
        }
    
    @pytest.mark.asyncio
    async def test_get_slack_webhook(self):
        """Test getting Slack webhook URL."""
        self.secret_manager.get_secret = AsyncMock(return_value="https://hooks.slack.com/test")
        
        webhook_url = await self.secret_manager.get_slack_webhook()
        assert webhook_url == "https://hooks.slack.com/test"
        
        # Verify correct secret name was requested
        self.secret_manager.get_secret.assert_called_once_with(
            "slack-webhook-url",
            fallback_env_var="SLACK_WEBHOOK_URL"
        )
    
    def test_get_health_status(self):
        """Test health status reporting."""
        status = self.secret_manager.get_health_status()
        
        assert "enabled" in status
        assert "client_initialized" in status
        assert "project_id" in status
        assert "cache_enabled" in status
        assert "timestamp" in status
    
    def test_cleanup_cache(self):
        """Test cache cleanup."""
        # Mock cache cleanup
        self.secret_manager.cache.clear_expired = Mock(return_value=5)
        
        stats = self.secret_manager.cleanup_cache()
        
        assert stats == {"cleared_entries": 5}
        self.secret_manager.cache.clear_expired.assert_called_once()


@pytest.mark.integration
class TestSecretManagerIntegration:
    """Integration tests for Secret Manager (requires actual GCP setup)."""
    
    @pytest.mark.skip(reason="Requires actual GCP credentials")
    @pytest.mark.asyncio
    async def test_real_gcp_integration(self):
        """Test with real GCP Secret Manager (manual test)."""
        # This test requires:
        # 1. Valid GCP project ID in environment
        # 2. Valid service account credentials
        # 3. Actual secrets in Secret Manager
        
        with patch.dict('os.environ', {
            'GCP_PROJECT_ID': 'your-test-project',
            'GOOGLE_APPLICATION_CREDENTIALS': 'path/to/service-account.json'
        }):
            sm = GoogleCloudSecretManager()
            
            if sm.enabled:
                # Test creating a test secret
                result = await sm.create_secret("test-integration-secret", "test-value")
                assert result is True
                
                # Test retrieving the secret
                value = await sm.get_secret("test-integration-secret")
                assert value == "test-value"
                
                # Test updating the secret
                result = await sm.update_secret("test-integration-secret", "updated-value")
                assert result is True
                
                # Test cleanup
                result = await sm.delete_secret("test-integration-secret")
                assert result is True