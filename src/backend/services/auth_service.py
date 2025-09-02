"""
Enhanced Schwab OAuth2 Authentication Service

Provides complete OAuth2 flow implementation for Schwab API integration
with secure token management, automatic refresh, and production-ready error handling.
"""

import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs
import aiohttp
import structlog
from pydantic import BaseModel, Field
from fastapi import HTTPException

from ..config import Settings

logger = structlog.get_logger()

class OAuthState(BaseModel):
    """OAuth state management model for CSRF protection."""
    state: str
    created_at: datetime
    expires_at: datetime
    client_id: Optional[str] = None

class TokenInfo(BaseModel):
    """OAuth token information with expiration handling."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str
    issued_at: datetime
    
    @property
    def expires_at(self) -> datetime:
        """Calculate absolute expiration time."""
        return self.issued_at + timedelta(seconds=self.expires_in)
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 5 minute buffer)."""
        return datetime.utcnow() >= self.expires_at - timedelta(minutes=5)

class SchwabOAuthService:
    """
    Enhanced Schwab OAuth2 integration service.
    
    Implements complete OAuth2 authorization code flow with:
    - Secure state parameter validation (CSRF protection)
    - Automatic token refresh
    - Token validation and user info retrieval
    - Production-ready error handling
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.client_id = self.settings.SCHWAB_CLIENT_ID
        self.client_secret = self.settings.SCHWAB_CLIENT_SECRET  
        self.redirect_uri = self.settings.SCHWAB_REDIRECT_URI
        self.base_url = "https://api.schwabapi.com"
        self.auth_url = "https://api.schwabapi.com/v1/oauth/authorize"
        self.token_url = "https://api.schwabapi.com/v1/oauth/token"
        
        # OAuth state storage (in production, use Redis or database)
        self._oauth_states: Dict[str, OAuthState] = {}
        self._user_tokens: Dict[str, TokenInfo] = {}
        
        logger.info("SchwabOAuthService initialized", 
                   client_id_configured=bool(self.client_id),
                   redirect_uri=self.redirect_uri)
    
    async def initiate_oauth_flow(self, user_id: Optional[str] = None) -> Dict[str, str]:
        """
        Initiate OAuth2 authorization code flow.
        
        Args:
            user_id: Optional user identifier for token storage
        
        Returns:
            Dict containing authorization_url, state, and expiration
        
        Raises:
            HTTPException: If OAuth initiation fails
        """
        try:
            # Validate configuration
            if not self.client_id or not self.client_secret:
                raise HTTPException(
                    status_code=500,
                    detail="Schwab OAuth credentials not configured. Check SCHWAB_CLIENT_ID and SCHWAB_CLIENT_SECRET."
                )
            
            # Generate secure state parameter for CSRF protection
            state = secrets.token_urlsafe(32)
            
            # Store state with expiration (10 minutes)
            oauth_state = OAuthState(
                state=state,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=10),
                client_id=user_id
            )
            self._oauth_states[state] = oauth_state
            
            # Build authorization URL with required parameters
            auth_params = {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "scope": "readonly",  # Schwab API scope for readonly access
                "state": state,
            }
            
            authorization_url = f"{self.auth_url}?{urlencode(auth_params)}"
            
            logger.info("OAuth flow initiated", 
                       state=state, 
                       user_id=user_id,
                       scope="readonly")
            
            return {
                "authorization_url": authorization_url,
                "state": state,
                "expires_at": oauth_state.expires_at.isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to initiate OAuth flow: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"OAuth initiation failed: {str(e)}"
            )
    
    async def complete_oauth_flow(self, code: str, state: str) -> TokenInfo:
        """
        Complete OAuth2 flow by exchanging authorization code for tokens.
        
        Args:
            code: Authorization code from Schwab OAuth callback
            state: State parameter for CSRF validation
            
        Returns:
            TokenInfo with access and refresh tokens
        
        Raises:
            HTTPException: If OAuth completion fails or state is invalid
        """
        try:
            # Validate state parameter (CSRF protection)
            if not await self._validate_oauth_state(state):
                logger.warning("Invalid OAuth state parameter received", state=state)
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid or expired OAuth state parameter. Please restart the authentication process."
                )
            
            # Exchange authorization code for tokens
            token_data = await self._exchange_code_for_tokens(code)
            
            # Create token info object
            token_info = TokenInfo(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data["expires_in"],
                scope=token_data.get("scope", ""),
                issued_at=datetime.utcnow()
            )
            
            # Store tokens for user (in production, encrypt and store in database)
            oauth_state = self._oauth_states.get(state)
            if oauth_state and oauth_state.client_id:
                self._user_tokens[oauth_state.client_id] = token_info
                logger.info("Tokens stored for user", 
                           user_id=oauth_state.client_id,
                           expires_at=token_info.expires_at.isoformat())
            
            # Clean up OAuth state
            del self._oauth_states[state]
            
            logger.info("OAuth flow completed successfully", 
                       token_expires_in=token_info.expires_in,
                       scope=token_info.scope)
            
            return token_info
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OAuth flow completion failed: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"OAuth completion failed: {str(e)}"
            )
    
    async def refresh_access_token(self, refresh_token: str) -> TokenInfo:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New TokenInfo with refreshed access token
        
        Raises:
            HTTPException: If token refresh fails
        """
        try:
            logger.info("Refreshing access token")
            
            token_data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.token_url,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        logger.error("Token refresh failed", 
                                   status=response.status, 
                                   response=response_text)
                        raise HTTPException(
                            status_code=401, 
                            detail="Token refresh failed. Please re-authenticate."
                        )
                    
                    response_data = await response.json()
            
            # Create new token info
            new_token_info = TokenInfo(
                access_token=response_data["access_token"],
                refresh_token=response_data.get("refresh_token", refresh_token),  # May not provide new refresh token
                token_type=response_data.get("token_type", "Bearer"),
                expires_in=response_data["expires_in"],
                scope=response_data.get("scope", ""),
                issued_at=datetime.utcnow()
            )
            
            logger.info("Access token refreshed successfully", 
                       expires_in=new_token_info.expires_in)
            
            return new_token_info
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise HTTPException(
                status_code=401, 
                detail=f"Token refresh failed: {str(e)}"
            )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Schwab API.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User information dictionary
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/v1/user/profile",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error("Failed to get user info", 
                                   status=response.status)
                        return {
                            "error": "Failed to retrieve user information",
                            "status": response.status
                        }
                    
                    user_data = await response.json()
                    logger.info("User info retrieved successfully")
                    return user_data
                    
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {"error": str(e)}
    
    async def validate_token(self, access_token: str) -> bool:
        """
        Validate access token by making a test API call.
        
        Args:
            access_token: Access token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/v1/user/profile",
                    headers=headers
                ) as response:
                    is_valid = response.status == 200
                    logger.debug("Token validation result", 
                               is_valid=is_valid, 
                               status=response.status)
                    return is_valid
                    
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False
    
    def get_stored_token(self, user_id: str) -> Optional[TokenInfo]:
        """
        Get stored token for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            TokenInfo if found, None otherwise
        """
        return self._user_tokens.get(user_id)
    
    def store_token(self, user_id: str, token_info: TokenInfo) -> None:
        """
        Store token for user.
        
        Args:
            user_id: User identifier
            token_info: Token information to store
        """
        self._user_tokens[user_id] = token_info
        logger.info("Token stored for user", 
                   user_id=user_id, 
                   expires_at=token_info.expires_at.isoformat())
    
    def clear_token(self, user_id: str) -> None:
        """
        Clear stored token for user.
        
        Args:
            user_id: User identifier
        """
        if user_id in self._user_tokens:
            del self._user_tokens[user_id]
            logger.info("Token cleared for user", user_id=user_id)
    
    async def _validate_oauth_state(self, state: str) -> bool:
        """Validate OAuth state parameter for CSRF protection."""
        if state not in self._oauth_states:
            logger.warning("Unknown OAuth state parameter", state=state)
            return False
        
        oauth_state = self._oauth_states[state]
        if datetime.utcnow() > oauth_state.expires_at:
            logger.warning("Expired OAuth state parameter", 
                         state=state, 
                         expired_at=oauth_state.expires_at)
            del self._oauth_states[state]
            return False
        
        return True
    
    async def _exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        logger.info("Exchanging authorization code for tokens")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status != 200:
                    response_text = await response.text()
                    logger.error("Token exchange failed", 
                               status=response.status, 
                               response=response_text)
                    raise Exception(f"Token exchange failed: HTTP {response.status}")
                
                response_json = await response.json()
                logger.info("Token exchange successful")
                return response_json


# Service instance for dependency injection
_oauth_service_instance: Optional[SchwabOAuthService] = None

def get_oauth_service() -> SchwabOAuthService:
    """Get OAuth service instance (singleton pattern)."""
    global _oauth_service_instance
    if _oauth_service_instance is None:
        _oauth_service_instance = SchwabOAuthService()
    return _oauth_service_instance