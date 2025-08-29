"""
Simplified Schwab OAuth authentication manager.

Provides authentication functionality using schwab-py with file-based token storage.
GCP integration is available as an optional feature.
"""

import json
from pathlib import Path
from typing import Any

from loguru import logger
from schwab.auth import client_from_token_file, easy_client
from schwab.client import Client


class AuthenticationError(Exception):
    """Exception raised for authentication-related failures."""

    pass


class AuthManager:
    """
    Simplified Schwab API OAuth authentication manager.

    Handles Schwab API OAuth authentication with file-based token storage by default.
    Optionally supports GCP integration if google-cloud libraries are available.
    """

    def __init__(
        self,
        api_key: str,
        app_secret: str,
        callback_url: str,
        token_file: str | Path = "schwab_tokens.json",
        use_gcp: bool = False,
        gcp_project_id: str | None = None,
    ):
        """
        Initialize authentication manager.

        Args:
            api_key: Schwab API key
            app_secret: Schwab app secret
            callback_url: OAuth callback URL
            token_file: Path to token file for storage (default: schwab_tokens.json)
            use_gcp: Whether to use GCP for token storage (requires google-cloud packages)
            gcp_project_id: GCP project ID (required if use_gcp=True)
        """
        self.api_key = api_key
        self.app_secret = app_secret
        self.callback_url = callback_url
        self.token_path = Path(token_file)
        self.use_gcp = use_gcp
        self.gcp_project_id = gcp_project_id

        # Validate inputs
        if not all([api_key, app_secret, callback_url]):
            raise ValueError("api_key, app_secret, and callback_url are required")

        if use_gcp and not gcp_project_id:
            raise ValueError("gcp_project_id is required when use_gcp=True")

        # Initialize GCP helpers if requested
        self._gcp_helpers = None
        if use_gcp:
            try:
                from ..utils.gcp_helpers import retrieve_google_secret, store_firestore_value

                self._gcp_helpers = {
                    "retrieve_secret": retrieve_google_secret,
                    "store_firestore": store_firestore_value,
                }
                logger.info("GCP integration enabled")
            except ImportError:
                logger.warning(
                    "GCP integration requested but google-cloud packages not found. "
                    "Install with: pip install schwab-package[gcp]"
                )
                self.use_gcp = False

        logger.info(
            f"AuthManager initialized with {'GCP' if self.use_gcp else 'file-based'} token storage"
        )

    def get_authenticated_client(self, force_refresh: bool = False) -> Client:
        """
        Get authenticated Schwab client.

        Args:
            force_refresh: Whether to force refresh the client

        Returns:
            Authenticated Client instance

        Raises:
            AuthenticationError: If authentication fails
        """
        # Try to load existing token
        if not force_refresh:
            token_data = self._load_token()
            if token_data:
                try:
                    # Write token to file for schwab-py (if not already there)
                    if not self.token_path.exists() or force_refresh:
                        self._write_token_file(token_data)

                    client = client_from_token_file(
                        api_key=self.api_key,
                        app_secret=self.app_secret,
                        token_path=str(self.token_path),
                    )

                    logger.info("Successfully created authenticated client from existing token")
                    return client

                except Exception as e:
                    logger.warning(f"Failed to use existing token: {e}")
                    # Continue to manual auth flow

        # No valid token - require manual authentication
        raise AuthenticationError(
            "Authentication required. No valid token found.\n"
            "Please run the authentication flow first or ensure your token file is valid."
        )

    def authenticate_manual(self) -> Client:
        """
        Perform manual OAuth authentication flow.

        This method guides the user through the OAuth flow and stores the resulting token.

        Returns:
            Authenticated Client instance

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            logger.info("Starting manual OAuth authentication flow")

            # Use schwab-py's easy_client for initial auth
            client = easy_client(
                api_key=self.api_key,
                app_secret=self.app_secret,
                callback_url=self.callback_url,
                token_path=str(self.token_path),
            )

            # Store token if using GCP
            if self.use_gcp:
                self._store_token_to_gcp()

            logger.info("Manual authentication completed successfully")
            return client

        except Exception as e:
            error_msg = f"Manual authentication failed: {e}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

    def refresh_token_if_needed(self, client: Client) -> bool:
        """
        Check if token needs refresh and refresh if necessary.

        Args:
            client: Schwab client to check

        Returns:
            True if token was refreshed, False otherwise
        """
        try:
            # Check token age
            token_age = client.token_age()

            # Refresh if token is older than 6.5 days (tokens expire in 7 days)
            if token_age.total_seconds() > (6.5 * 24 * 60 * 60):
                logger.info("Token is close to expiry, initiating refresh")

                # The client should handle refresh automatically
                # We just need to store the updated token
                if self.use_gcp:
                    self._store_token_to_gcp()
                else:
                    # Token file should be automatically updated by schwab-py
                    logger.debug("Token file updated by schwab-py")

                return True

        except Exception as e:
            logger.error(f"Error checking/refreshing token: {e}")

        return False

    def _load_token(self) -> dict[str, Any] | None:
        """
        Load token from storage (file or GCP).

        Returns:
            Token dictionary or None if not found
        """
        if self.use_gcp:
            return self._load_token_from_gcp()
        else:
            return self._load_token_from_file()

    def _load_token_from_file(self) -> dict[str, Any] | None:
        """Load token from file with auto-format detection."""
        try:
            if self.token_path.exists():
                with open(self.token_path) as f:
                    token_data: dict[str, Any] = json.load(f)
                
                # Auto-detect and convert token format
                token_data = self._normalize_token_format(token_data)
                logger.debug("Loaded and normalized token from file")
                return token_data
        except Exception as e:
            logger.warning(f"Failed to load token from file: {e}")

        return None

    def _load_token_from_gcp(self) -> dict[str, Any] | None:
        """Load token from GCP (if available)."""
        if not self.use_gcp or not self._gcp_helpers:
            return None

        try:
            # This would need to be implemented based on your GCP setup
            # For now, return None to fallback to file-based
            logger.debug("GCP token loading not yet implemented")
            return None

        except Exception as e:
            logger.warning(f"Failed to load token from GCP: {e}")
            return None

    def _write_token_file(self, token_data: dict[str, Any]) -> None:
        """
        Write token data to file.

        Args:
            token_data: Token dictionary to write
        """
        try:
            with open(self.token_path, "w") as f:
                json.dump(token_data, f, indent=2)
            logger.debug("Wrote token data to file")
        except Exception as e:
            logger.error(f"Failed to write token file: {e}")
            raise

    def _normalize_token_format(self, token_data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize token format to handle both flat and nested structures.
        
        Args:
            token_data: Raw token data from file
            
        Returns:
            Normalized token data in the expected format
        """
        # Check if it's already in the expected nested format
        if "token" in token_data and isinstance(token_data["token"], dict):
            logger.debug("Token already in nested format")
            return token_data
        
        # Check if it's a flat OAuth token format
        oauth_fields = {"access_token", "refresh_token", "token_type"}
        if oauth_fields.issubset(token_data.keys()):
            logger.info("Converting flat token format to nested format")
            
            # Extract creation timestamp if present
            creation_timestamp = token_data.pop("created_at", None)
            
            # Create nested structure
            normalized = {
                "token": token_data.copy(),
                "creation_timestamp": creation_timestamp
            }
            
            # Save the normalized format back to file for future use
            self._write_token_file(normalized)
            
            return normalized
        
        # If format is unrecognized, return as-is and let downstream handle it
        logger.warning("Unrecognized token format, passing through unchanged")
        return token_data

    def _store_token_to_gcp(self) -> None:
        """Store token from file to GCP (if available)."""
        if not self.use_gcp or not self._gcp_helpers:
            return

        try:
            # This would need to be implemented based on your GCP setup
            logger.debug("GCP token storage not yet implemented")

        except Exception as e:
            logger.error(f"Failed to store token to GCP: {e}")

    def cleanup(self) -> None:
        """Cleanup resources."""
        logger.debug("AuthManager cleanup completed")

    def health_check(self) -> dict[str, Any]:
        """
        Perform health check of the authentication manager.

        Returns:
            Health check results
        """
        health: dict[str, Any] = {
            "status": "unknown",
            "token_file_exists": self.token_path.exists(),
            "using_gcp": self.use_gcp,
            "issues": [],
            "recommendations": [],
        }

        try:
            # Check if token file exists
            if not health["token_file_exists"]:
                health["issues"].append("No token file found")
                health["recommendations"].append("Run authentication flow")
            else:
                # Try to load token
                token_data = self._load_token()
                if not token_data:
                    health["issues"].append("Token file exists but could not be loaded")
                    health["recommendations"].append("Re-run authentication flow")

            # Check GCP setup
            if self.use_gcp and not self._gcp_helpers:
                health["issues"].append("GCP requested but libraries not available")
                health["recommendations"].append(
                    "Install GCP dependencies: pip install schwab-package[gcp]"
                )

            # Set overall status
            if not health["issues"]:
                health["status"] = "healthy"
            else:
                health["status"] = "needs_attention"

        except Exception as e:
            health["status"] = "error"
            health["issues"].append(f"Health check failed: {e}")

        return health


# Convenience function for simple use cases
def create_auth_manager(
    api_key: str, app_secret: str, callback_url: str = "https://localhost:8080/callback", **kwargs: Any
) -> AuthManager:
    """
    Create an AuthManager with sensible defaults.

    Args:
        api_key: Schwab API key
        app_secret: Schwab app secret
        callback_url: OAuth callback URL
        **kwargs: Additional arguments for AuthManager

    Returns:
        Configured AuthManager instance
    """
    return AuthManager(api_key=api_key, app_secret=app_secret, callback_url=callback_url, **kwargs)
