"""
Enhanced Authentication API endpoints for Schwab OAuth2 flow.

Provides complete OAuth2 integration with secure token management,
automatic refresh, and production-ready authentication workflow.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog
import secrets

from ..services.auth_service import SchwabOAuthService, get_oauth_service, TokenInfo
from ..config import Settings

logger = structlog.get_logger()

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Request/Response Models
class OAuthInitiationResponse(BaseModel):
    """Response model for OAuth flow initiation."""
    authorization_url: str
    state: str
    expires_at: str
    demo_mode: bool = False

class OAuthCompletionRequest(BaseModel):
    """Request model for OAuth flow completion."""
    code: str = Field(..., description="Authorization code from Schwab")
    state: str = Field(..., description="State parameter for CSRF validation")

class TokenResponse(BaseModel):
    """Response model for successful token operations."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str
    user_info: Dict[str, Any]
    demo_mode: bool = False

class AuthStatusResponse(BaseModel):
    """Response model for authentication status."""
    is_authenticated: bool
    user_info: Optional[Dict[str, Any]] = None
    token_expires_at: Optional[str] = None
    demo_mode: bool = False
    connection_status: str = "unknown"

class TokenRefreshRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str = Field(..., description="Valid refresh token")

class LogoutResponse(BaseModel):
    """Response model for logout."""
    success: bool
    message: str

# Dependency functions
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

@router.post("/oauth/initiate", response_model=OAuthInitiationResponse)
async def initiate_oauth_flow(
    user_id: str = "default_user",  # In production, get from JWT or session
    oauth_service: SchwabOAuthService = Depends(get_oauth_service),
    settings: Settings = Depends(get_settings)
) -> OAuthInitiationResponse:
    """
    Initiate Schwab OAuth2 authorization flow.
    
    This endpoint starts the OAuth2 flow by generating a secure authorization URL
    with CSRF protection via state parameter.
    
    Args:
        user_id: User identifier for token storage
        oauth_service: OAuth service dependency
        settings: Application settings
    
    Returns:
        Authorization URL, state parameter, and expiration info
    
    Raises:
        HTTPException: If OAuth initiation fails
    """
    try:
        logger.info("Initiating OAuth flow", user_id=user_id, demo_mode=settings.DEMO_MODE)
        
        # Check if demo mode is enabled
        if settings.DEMO_MODE:
            logger.info("Demo mode enabled, providing mock OAuth response")
            return OAuthInitiationResponse(
                authorization_url="https://demo.schwab.com/oauth/authorize?demo=true",
                state="demo_state",
                expires_at="2024-12-31T23:59:59Z",
                demo_mode=True
            )
        
        # Initiate real OAuth flow
        result = await oauth_service.initiate_oauth_flow(user_id)
        
        return OAuthInitiationResponse(
            authorization_url=result["authorization_url"],
            state=result["state"],
            expires_at=result["expires_at"],
            demo_mode=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth initiation failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"OAuth initiation failed: {str(e)}"
        )

@router.post("/oauth/complete", response_model=TokenResponse)
async def complete_oauth_flow(
    request: OAuthCompletionRequest,
    oauth_service: SchwabOAuthService = Depends(get_oauth_service),
    settings: Settings = Depends(get_settings)
) -> TokenResponse:
    """
    Complete Schwab OAuth2 authorization flow.
    
    This endpoint handles the OAuth callback, exchanges the authorization code
    for access/refresh tokens, and retrieves user information.
    
    Args:
        request: OAuth completion request with code and state
        oauth_service: OAuth service dependency
        settings: Application settings
    
    Returns:
        Access token, user info, and token metadata
    
    Raises:
        HTTPException: If OAuth completion fails
    """
    try:
        logger.info("Completing OAuth flow", 
                   code_length=len(request.code), 
                   state=request.state,
                   demo_mode=settings.DEMO_MODE)
        
        # Handle demo mode
        if settings.DEMO_MODE or request.state == "demo_state":
            logger.info("Demo mode OAuth completion")
            return TokenResponse(
                access_token="demo_access_token_" + secrets.token_hex(16),
                token_type="Bearer",
                expires_in=3600,
                scope="MarketData",
                user_info={
                    "id": "demo_user",
                    "name": "Demo User",
                    "email": "demo@tradeassist.local",
                    "account_type": "Demo Account"
                },
                demo_mode=True
            )
        
        # Complete real OAuth flow
        token_info = await oauth_service.complete_oauth_flow(request.code, request.state)
        
        # Get user information with the new token
        user_info = await oauth_service.get_user_info(token_info.access_token)
        
        return TokenResponse(
            access_token=token_info.access_token,
            token_type=token_info.token_type,
            expires_in=token_info.expires_in,
            scope=token_info.scope,
            user_info=user_info,
            demo_mode=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth completion failed: {e}")
        raise HTTPException(
            status_code=400, 
            detail=f"OAuth completion failed: {str(e)}"
        )

@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    oauth_service: SchwabOAuthService = Depends(get_oauth_service),
    settings: Settings = Depends(get_settings)
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    
    This endpoint handles automatic token refresh to maintain
    continuous authentication without user intervention.
    
    Args:
        request: Token refresh request
        oauth_service: OAuth service dependency
        settings: Application settings
    
    Returns:
        New access token and metadata
    
    Raises:
        HTTPException: If token refresh fails
    """
    try:
        logger.info("Refreshing access token", demo_mode=settings.DEMO_MODE)
        
        # Handle demo mode
        if settings.DEMO_MODE or request.refresh_token.startswith("demo_"):
            logger.info("Demo mode token refresh")
            return TokenResponse(
                access_token="demo_access_token_" + secrets.token_hex(16),
                token_type="Bearer",
                expires_in=3600,
                scope="MarketData",
                user_info={
                    "id": "demo_user",
                    "name": "Demo User",
                    "email": "demo@tradeassist.local",
                    "account_type": "Demo Account"
                },
                demo_mode=True
            )
        
        # Refresh real token
        token_info = await oauth_service.refresh_access_token(request.refresh_token)
        
        # Get updated user information
        user_info = await oauth_service.get_user_info(token_info.access_token)
        
        return TokenResponse(
            access_token=token_info.access_token,
            token_type=token_info.token_type,
            expires_in=token_info.expires_in,
            scope=token_info.scope,
            user_info=user_info,
            demo_mode=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=401, 
            detail=f"Token refresh failed: {str(e)}"
        )

@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(
    user_id: str = "default_user",  # In production, extract from JWT or session
    oauth_service: SchwabOAuthService = Depends(get_oauth_service),
    settings: Settings = Depends(get_settings)
) -> AuthStatusResponse:
    """
    Get current authentication status for user.
    
    This endpoint checks the user's authentication state,
    token validity, and connection status.
    
    Args:
        user_id: User identifier
        oauth_service: OAuth service dependency
        settings: Application settings
    
    Returns:
        Authentication status and user information
    """
    try:
        logger.debug("Checking auth status", user_id=user_id, demo_mode=settings.DEMO_MODE)
        
        # Handle demo mode
        if settings.DEMO_MODE:
            return AuthStatusResponse(
                is_authenticated=True,
                user_info={
                    "id": "demo_user",
                    "name": "Demo User",
                    "email": "demo@tradeassist.local",
                    "account_type": "Demo Account"
                },
                demo_mode=True,
                connection_status="connected"
            )
        
        # Check real authentication status
        stored_token = oauth_service.get_stored_token(user_id)
        if not stored_token:
            return AuthStatusResponse(
                is_authenticated=False,
                demo_mode=False,
                connection_status="not_authenticated"
            )
        
        # Check if token is expired
        if stored_token.is_expired:
            logger.info("Stored token is expired", user_id=user_id)
            oauth_service.clear_token(user_id)
            return AuthStatusResponse(
                is_authenticated=False,
                demo_mode=False,
                connection_status="token_expired"
            )
        
        # Validate token with Schwab API
        is_valid = await oauth_service.validate_token(stored_token.access_token)
        if not is_valid:
            logger.warning("Stored token validation failed", user_id=user_id)
            oauth_service.clear_token(user_id)
            return AuthStatusResponse(
                is_authenticated=False,
                demo_mode=False,
                connection_status="token_invalid"
            )
        
        # Get current user info
        user_info = await oauth_service.get_user_info(stored_token.access_token)
        
        return AuthStatusResponse(
            is_authenticated=True,
            user_info=user_info,
            token_expires_at=stored_token.expires_at.isoformat(),
            demo_mode=False,
            connection_status="connected"
        )
        
    except Exception as e:
        logger.error(f"Auth status check failed: {e}")
        return AuthStatusResponse(
            is_authenticated=False,
            demo_mode=settings.DEMO_MODE,
            connection_status="error"
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout(
    user_id: str = "default_user",  # In production, extract from JWT or session
    oauth_service: SchwabOAuthService = Depends(get_oauth_service)
) -> LogoutResponse:
    """
    Logout user and clear stored tokens.
    
    This endpoint clears the user's stored authentication tokens,
    effectively logging them out of the application.
    
    Args:
        user_id: User identifier
        oauth_service: OAuth service dependency
    
    Returns:
        Logout success status
    """
    try:
        logger.info("Logging out user", user_id=user_id)
        
        # Clear stored tokens
        oauth_service.clear_token(user_id)
        
        return LogoutResponse(
            success=True,
            message="Successfully logged out"
        )
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return LogoutResponse(
            success=False,
            message=f"Logout failed: {str(e)}"
        )

# Legacy endpoints for backward compatibility
@router.post("/schwab/authenticate")
async def start_schwab_authentication(request: Request) -> Dict[str, Any]:
    """
    Legacy endpoint for backward compatibility.
    Redirects to new OAuth flow.
    """
    logger.warning("Legacy authentication endpoint called, use /oauth/initiate instead")
    
    try:
        oauth_service = get_oauth_service()
        result = await oauth_service.initiate_oauth_flow()
        
        return {
            "status": "redirect_required",
            "message": "Please use the new OAuth flow",
            "authorization_url": result["authorization_url"],
            "instructions": "Visit the authorization_url to complete authentication"
        }
    except Exception as e:
        logger.error(f"Legacy authentication failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/schwab/status")
async def get_authentication_status(request: Request) -> Dict[str, Any]:
    """
    Legacy endpoint for backward compatibility.
    Redirects to new status endpoint.
    """
    logger.warning("Legacy status endpoint called, use /status instead")
    
    settings = Settings()
    if settings.DEMO_MODE:
        return {
            "authenticated": True,
            "connected": True,
            "status": "demo_mode",
            "demo_mode": True
        }
    
    return {
        "authenticated": False,
        "connected": False,
        "status": "use_new_oauth_flow",
        "message": "Please use the new OAuth endpoints at /api/auth/"
    }