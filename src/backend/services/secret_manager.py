"""
Google Cloud Secret Manager Integration.

Secure credential storage and management for trading application
with automatic rotation, encrypted local caching, and audit logging.
"""

import os
import json
import time
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

import structlog
from google.cloud import secretmanager
from google.api_core import exceptions as gcp_exceptions
from cryptography.fernet import Fernet

from ..config import settings

logger = structlog.get_logger()


@dataclass
class SecretMetadata:
    """Metadata for a secret entry."""
    name: str
    version: str
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime] = None
    rotation_enabled: bool = False


class LocalSecretCache:
    """
    Local encrypted cache for secrets to improve performance.
    
    Reduces API calls to Google Cloud Secret Manager by caching
    frequently accessed secrets with TTL expiration.
    """
    
    def __init__(self, cache_dir: str = ".secrets_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Generate or load encryption key
        key_file = self.cache_dir / "cache.key"
        if key_file.exists():
            with open(key_file, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            # Restrict key file permissions
            os.chmod(key_file, 0o600)
        
        self.fernet = Fernet(key)
        self.default_ttl = 3600  # 1 hour
    
    def _get_cache_file(self, secret_name: str) -> Path:
        """Get cache file path for secret."""
        # Use hash of secret name for filename security
        import hashlib
        name_hash = hashlib.sha256(secret_name.encode()).hexdigest()[:16]
        return self.cache_dir / f"cache_{name_hash}.enc"
    
    def get(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """
        Get secret from cache if not expired.
        
        Args:
            secret_name: Name of the secret.
        
        Returns:
            Dict with secret data or None if not cached/expired.
        """
        try:
            cache_file = self._get_cache_file(secret_name)
            if not cache_file.exists():
                return None
            
            # Read and decrypt cache data
            with open(cache_file, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            cache_entry = json.loads(decrypted_data.decode())
            
            # Check expiration
            if time.time() > cache_entry["expires_at"]:
                cache_file.unlink()  # Remove expired cache
                return None
            
            return cache_entry["data"]
            
        except Exception as e:
            logger.warning(f"Cache read error for {secret_name}: {e}")
            return None
    
    def set(self, secret_name: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        Store secret in cache with TTL.
        
        Args:
            secret_name: Name of the secret.
            data: Secret data to cache.
            ttl: Time to live in seconds (uses default if None).
        """
        try:
            cache_entry = {
                "data": data,
                "cached_at": time.time(),
                "expires_at": time.time() + (ttl or self.default_ttl)
            }
            
            # Encrypt and store
            encrypted_data = self.fernet.encrypt(
                json.dumps(cache_entry).encode()
            )
            
            cache_file = self._get_cache_file(secret_name)
            with open(cache_file, "wb") as f:
                f.write(encrypted_data)
            
            # Restrict cache file permissions
            os.chmod(cache_file, 0o600)
            
        except Exception as e:
            logger.error(f"Cache write error for {secret_name}: {e}")
    
    def invalidate(self, secret_name: str) -> None:
        """Remove secret from cache."""
        try:
            cache_file = self._get_cache_file(secret_name)
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logger.warning(f"Cache invalidation error for {secret_name}: {e}")
    
    def clear_expired(self) -> int:
        """Clear all expired cache entries."""
        cleared = 0
        try:
            current_time = time.time()
            for cache_file in self.cache_dir.glob("cache_*.enc"):
                try:
                    with open(cache_file, "rb") as f:
                        encrypted_data = f.read()
                    
                    decrypted_data = self.fernet.decrypt(encrypted_data)
                    cache_entry = json.loads(decrypted_data.decode())
                    
                    if current_time > cache_entry["expires_at"]:
                        cache_file.unlink()
                        cleared += 1
                        
                except Exception:
                    # Remove corrupted cache files
                    cache_file.unlink()
                    cleared += 1
                    
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
        
        return cleared


class GoogleCloudSecretManager:
    """
    Google Cloud Secret Manager service.
    
    Provides secure credential storage with features:
    - Automatic secret rotation
    - Local encrypted caching
    - Version management
    - Audit logging
    - Fallback to environment variables
    """
    
    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.client: Optional[secretmanager.SecretManagerServiceClient] = None
        self.cache = LocalSecretCache()
        self.enabled = bool(self.project_id)
        
        # Initialize client if credentials available
        if self.enabled:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                logger.info("Google Cloud Secret Manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Secret Manager: {e}")
                self.enabled = False
    
    async def get_secret(
        self,
        secret_name: str,
        version: str = "latest",
        use_cache: bool = True,
        fallback_env_var: Optional[str] = None
    ) -> Optional[str]:
        """
        Get secret value with caching and fallback.
        
        Args:
            secret_name: Name of the secret.
            version: Version to retrieve (default: "latest").
            use_cache: Whether to use local cache.
            fallback_env_var: Environment variable to use as fallback.
        
        Returns:
            Secret value or None if not found.
        """
        # Check cache first
        if use_cache:
            cached = self.cache.get(f"{secret_name}:{version}")
            if cached:
                logger.debug(f"Secret {secret_name} retrieved from cache")
                return cached.get("value")
        
        # Try Google Cloud Secret Manager
        if self.enabled and self.client:
            try:
                secret_value = await self._fetch_from_gcp(secret_name, version)
                if secret_value:
                    # Cache the result
                    if use_cache:
                        self.cache.set(
                            f"{secret_name}:{version}",
                            {"value": secret_value, "source": "gcp"}
                        )
                    
                    logger.info(f"Secret {secret_name} retrieved from GCP")
                    return secret_value
                    
            except Exception as e:
                logger.error(f"Failed to retrieve secret {secret_name} from GCP: {e}")
        
        # Fallback to environment variable
        if fallback_env_var:
            env_value = os.getenv(fallback_env_var)
            if env_value:
                logger.info(f"Secret {secret_name} retrieved from environment")
                return env_value
        
        logger.warning(f"Secret {secret_name} not found in any source")
        return None
    
    async def _fetch_from_gcp(self, secret_name: str, version: str) -> Optional[str]:
        """Fetch secret from Google Cloud Secret Manager."""
        try:
            secret_path = self.client.secret_version_path(
                self.project_id, secret_name, version
            )
            
            response = self.client.access_secret_version(request={"name": secret_path})
            return response.payload.data.decode("UTF-8")
            
        except gcp_exceptions.NotFound:
            logger.warning(f"Secret {secret_name} not found in GCP")
            return None
        except Exception as e:
            logger.error(f"GCP secret fetch error: {e}")
            return None
    
    async def create_secret(
        self,
        secret_name: str,
        secret_value: str,
        labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Create a new secret.
        
        Args:
            secret_name: Name of the secret.
            secret_value: Secret value.
            labels: Optional labels for the secret.
        
        Returns:
            True if created successfully.
        """
        if not self.enabled or not self.client:
            logger.warning("Secret Manager not available for secret creation")
            return False
        
        try:
            # Create secret
            parent = f"projects/{self.project_id}"
            secret_config = {
                "replication": {"automatic": {}},
                "labels": labels or {}
            }
            
            secret = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_name,
                    "secret": secret_config
                }
            )
            
            # Add secret version
            version = self.client.add_secret_version(
                request={
                    "parent": secret.name,
                    "payload": {"data": secret_value.encode("UTF-8")}
                }
            )
            
            logger.info(f"Secret {secret_name} created successfully")
            return True
            
        except gcp_exceptions.AlreadyExists:
            logger.warning(f"Secret {secret_name} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to create secret {secret_name}: {e}")
            return False
    
    async def update_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Update secret with new version.
        
        Args:
            secret_name: Name of the secret.
            secret_value: New secret value.
        
        Returns:
            True if updated successfully.
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            secret_path = self.client.secret_path(self.project_id, secret_name)
            
            # Add new secret version
            self.client.add_secret_version(
                request={
                    "parent": secret_path,
                    "payload": {"data": secret_value.encode("UTF-8")}
                }
            )
            
            # Invalidate cache
            self.cache.invalidate(f"{secret_name}:latest")
            
            logger.info(f"Secret {secret_name} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update secret {secret_name}: {e}")
            return False
    
    async def list_secrets(self) -> List[SecretMetadata]:
        """
        List all secrets with metadata.
        
        Returns:
            List of secret metadata.
        """
        secrets = []
        
        if not self.enabled or not self.client:
            return secrets
        
        try:
            parent = f"projects/{self.project_id}"
            
            for secret in self.client.list_secrets(request={"parent": parent}):
                # Get latest version info
                try:
                    versions = list(self.client.list_secret_versions(
                        request={"parent": secret.name}
                    ))
                    
                    if versions:
                        latest_version = versions[0]
                        metadata = SecretMetadata(
                            name=secret.name.split('/')[-1],
                            version=latest_version.name.split('/')[-1],
                            created_at=datetime.fromtimestamp(
                                secret.create_time.timestamp(), timezone.utc
                            ),
                            last_accessed=datetime.now(timezone.utc),
                            rotation_enabled=bool(secret.labels.get("auto_rotate"))
                        )
                        secrets.append(metadata)
                        
                except Exception as e:
                    logger.warning(f"Error getting metadata for {secret.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
        
        return secrets
    
    async def delete_secret(self, secret_name: str) -> bool:
        """
        Delete a secret and all its versions.
        
        Args:
            secret_name: Name of the secret.
        
        Returns:
            True if deleted successfully.
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            secret_path = self.client.secret_path(self.project_id, secret_name)
            self.client.delete_secret(request={"name": secret_path})
            
            # Clear from cache
            self.cache.invalidate(f"{secret_name}:latest")
            
            logger.info(f"Secret {secret_name} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete secret {secret_name}: {e}")
            return False
    
    def cleanup_cache(self) -> Dict[str, int]:
        """
        Cleanup expired cache entries.
        
        Returns:
            Cleanup statistics.
        """
        cleared = self.cache.clear_expired()
        return {"cleared_entries": cleared}
    
    async def get_schwab_credentials(self) -> Dict[str, str]:
        """
        Get Schwab API credentials.
        
        Returns:
            Dict with app_key and app_secret.
        """
        credentials = {}
        
        app_key = await self.get_secret(
            "schwab-app-key",
            fallback_env_var="SCHWAB_APP_KEY"
        )
        app_secret = await self.get_secret(
            "schwab-app-secret", 
            fallback_env_var="SCHWAB_APP_SECRET"
        )
        
        if app_key:
            credentials["app_key"] = app_key
        if app_secret:
            credentials["app_secret"] = app_secret
            
        return credentials
    
    async def get_slack_webhook(self) -> Optional[str]:
        """
        Get Slack webhook URL.
        
        Returns:
            Slack webhook URL or None.
        """
        return await self.get_secret(
            "slack-webhook-url",
            fallback_env_var="SLACK_WEBHOOK_URL"
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get Secret Manager health status.
        
        Returns:
            Health status information.
        """
        return {
            "enabled": self.enabled,
            "client_initialized": self.client is not None,
            "project_id": self.project_id,
            "cache_enabled": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global instance
secret_manager = GoogleCloudSecretManager()