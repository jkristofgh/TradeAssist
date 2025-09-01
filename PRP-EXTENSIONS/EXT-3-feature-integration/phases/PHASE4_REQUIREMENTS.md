# Phase 4: Authentication Integration & OAuth Flow

## Phase Overview
- **Phase Name**: Authentication Integration & OAuth Flow
- **Phase Number**: 4 of 4 (Final)
- **Estimated Duration**: 4-6 days
- **Implementation Effort**: 20% of total extension
- **Primary Focus**: Implement complete Schwab OAuth flow with secure token management and production-ready authentication

## Phase Objectives

### Primary Goals
1. **Complete OAuth Flow Implementation**: Frontend OAuth initiation and callback handling
2. **Secure Token Management**: Automatic token refresh and secure storage
3. **Authentication State Management**: Global authentication context and status display
4. **Authenticated API Integration**: Secure API calls for all analytics endpoints  
5. **Production Readiness**: Error handling, security, and demo mode preservation

### Success Criteria
- [ ] Complete Schwab OAuth flow functional from frontend
- [ ] Authentication status properly displayed and managed
- [ ] Token refresh handled automatically and transparently
- [ ] Authentication errors provide clear user guidance  
- [ ] Demo mode continues working for development/testing

## Prerequisites from Phase 3
- [x] Reliable WebSocket infrastructure for authenticated streaming
- [x] Real-time analytics data streaming to dashboard
- [x] Typed message system ready for authenticated channels
- [x] Complete analytics functionality accessible through UI

## Technical Requirements

### Backend Authentication Enhancement

#### 1. OAuth Service Implementation
```python
# src/backend/services/auth_service.py

import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs
import aiohttp
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

class OAuthState(BaseModel):
    """OAuth state management model."""
    state: str
    created_at: datetime
    expires_at: datetime
    client_id: Optional[str] = None

class TokenInfo(BaseModel):
    """OAuth token information."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str
    issued_at: datetime
    
    @property
    def expires_at(self) -> datetime:
        return self.issued_at + timedelta(seconds=self.expires_in)
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.expires_at - timedelta(minutes=5)  # 5 minute buffer

class SchwabOAuthService:
    """Enhanced Schwab OAuth integration service."""
    
    def __init__(self):
        self.client_id = settings.SCHWAB_CLIENT_ID
        self.client_secret = settings.SCHWAB_CLIENT_SECRET  
        self.redirect_uri = settings.SCHWAB_REDIRECT_URI
        self.base_url = "https://api.schwabapi.com"
        self.auth_url = "https://api.schwabapi.com/oauth/authorize"
        self.token_url = "https://api.schwabapi.com/oauth/token"
        
        # OAuth state storage (in production, use Redis or database)
        self._oauth_states: Dict[str, OAuthState] = {}
        self._user_tokens: Dict[str, TokenInfo] = {}
        
    async def initiate_oauth_flow(self, user_id: Optional[str] = None) -> Dict[str, str]:
        """
        Initiate OAuth flow and return authorization URL.
        
        Returns:
            Dict containing authorization_url and state parameter
        """
        try:
            # Generate secure state parameter
            state = secrets.token_urlsafe(32)
            
            # Store state with expiration
            oauth_state = OAuthState(
                state=state,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=10),
                client_id=user_id
            )
            self._oauth_states[state] = oauth_state
            
            # Build authorization URL
            auth_params = {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "scope": "MarketData",  # Schwab API scope
                "state": state,
            }
            
            authorization_url = f"{self.auth_url}?{urlencode(auth_params)}"
            
            logger.info(f"OAuth flow initiated", state=state, user_id=user_id)
            
            return {
                "authorization_url": authorization_url,
                "state": state,
                "expires_at": oauth_state.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to initiate OAuth flow: {e}")
            raise HTTPException(status_code=500, detail="OAuth initiation failed")
    
    async def complete_oauth_flow(self, code: str, state: str) -> TokenInfo:
        """
        Complete OAuth flow by exchanging authorization code for tokens.
        
        Args:
            code: Authorization code from Schwab
            state: State parameter for validation
            
        Returns:
            TokenInfo with access and refresh tokens
        """
        try:
            # Validate state parameter
            if not await self._validate_oauth_state(state):
                raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
            
            # Exchange authorization code for tokens
            token_data = await self._exchange_code_for_tokens(code)
            
            # Create token info
            token_info = TokenInfo(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data["expires_in"],
                scope=token_data.get("scope", ""),
                issued_at=datetime.utcnow()
            )
            
            # Store tokens (in production, encrypt and store in database)
            oauth_state = self._oauth_states.get(state)
            if oauth_state and oauth_state.client_id:
                self._user_tokens[oauth_state.client_id] = token_info
            
            # Clean up OAuth state
            del self._oauth_states[state]
            
            logger.info("OAuth flow completed successfully")
            return token_info
            
        except Exception as e:
            logger.error(f"OAuth flow completion failed: {e}")
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=400, detail=f"OAuth completion failed: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> TokenInfo:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New TokenInfo with refreshed tokens
        """
        try:
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
                        logger.error(f"Token refresh failed: {response.status} {response_text}")
                        raise HTTPException(status_code=401, detail="Token refresh failed")
                    
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
            
            logger.info("Access token refreshed successfully")
            return new_token_info
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise HTTPException(status_code=401, detail="Token refresh failed")
    
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
                        logger.error(f"Failed to get user info: {response.status}")
                        return {"error": "Failed to retrieve user information"}
                    
                    user_data = await response.json()
                    return user_data
                    
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {"error": str(e)}
    
    async def validate_token(self, access_token: str) -> bool:
        """Validate access token by making a test API call."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/v1/user/profile",
                    headers=headers
                ) as response:
                    return response.status == 200
                    
        except Exception:
            return False
    
    async def _validate_oauth_state(self, state: str) -> bool:
        """Validate OAuth state parameter."""
        if state not in self._oauth_states:
            return False
        
        oauth_state = self._oauth_states[state]
        if datetime.utcnow() > oauth_state.expires_at:
            del self._oauth_states[state]
            return False
        
        return True
    
    async def _exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens."""
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
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
                    logger.error(f"Token exchange failed: {response.status} {response_text}")
                    raise Exception(f"Token exchange failed: {response.status}")
                
                return await response.json()
```

#### 2. Enhanced API Router
```python
# src/backend/api/auth.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..services.auth_service import SchwabOAuthService, TokenInfo

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Request/Response Models
class OAuthInitiationResponse(BaseModel):
    authorization_url: str
    state: str
    expires_at: str

class OAuthCompletionRequest(BaseModel):
    code: str
    state: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str
    user_info: dict

class AuthStatusResponse(BaseModel):
    is_authenticated: bool
    user_info: Optional[dict] = None
    token_expires_at: Optional[str] = None
    demo_mode: bool = False

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# Service dependency
def get_oauth_service() -> SchwabOAuthService:
    return SchwabOAuthService()

@router.post("/oauth/initiate", response_model=OAuthInitiationResponse)
async def initiate_oauth_flow(
    oauth_service: SchwabOAuthService = Depends(get_oauth_service)
):
    """Initiate Schwab OAuth flow."""
    try:
        result = await oauth_service.initiate_oauth_flow()
        return OAuthInitiationResponse(**result)
    except Exception as e:
        logger.error(f"OAuth initiation failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth initiation failed")

@router.post("/oauth/complete", response_model=TokenResponse)
async def complete_oauth_flow(
    request: OAuthCompletionRequest,
    oauth_service: SchwabOAuthService = Depends(get_oauth_service)
):
    """Complete Schwab OAuth flow."""
    try:
        token_info = await oauth_service.complete_oauth_flow(request.code, request.state)
        user_info = await oauth_service.get_user_info(token_info.access_token)
        
        return TokenResponse(
            access_token=token_info.access_token,
            token_type=token_info.token_type,
            expires_in=token_info.expires_in,
            scope=token_info.scope,
            user_info=user_info
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth completion failed: {e}")
        raise HTTPException(status_code=400, detail=f"OAuth completion failed: {str(e)}")

@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    oauth_service: SchwabOAuthService = Depends(get_oauth_service)
):
    """Refresh access token."""
    try:
        token_info = await oauth_service.refresh_access_token(request.refresh_token)
        user_info = await oauth_service.get_user_info(token_info.access_token)
        
        return TokenResponse(
            access_token=token_info.access_token,
            token_type=token_info.token_type,
            expires_in=token_info.expires_in,
            scope=token_info.scope,
            user_info=user_info
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Token refresh failed")

@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(
    # In production, extract user from JWT token or session
    user_id: str = "default_user",
    oauth_service: SchwabOAuthService = Depends(get_oauth_service)
):
    """Get current authentication status."""
    try:
        # Check if user has valid tokens (implement based on your storage)
        # This is a simplified example
        
        return AuthStatusResponse(
            is_authenticated=False,  # Implement actual logic
            demo_mode=settings.DEMO_MODE
        )
    except Exception as e:
        logger.error(f"Auth status check failed: {e}")
        return AuthStatusResponse(
            is_authenticated=False,
            demo_mode=settings.DEMO_MODE
        )
```

### Frontend Authentication System

#### 1. Authentication Context
```typescript
// src/frontend/src/context/AuthContext.tsx

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { apiClient } from '../services/apiClient';

interface User {
  id?: string;
  name?: string;
  email?: string;
  accountType?: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  tokenExpiresAt: Date | null;
  isLoading: boolean;
  error: string | null;
  demoMode: boolean;
}

type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; accessToken: string; refreshToken: string; expiresIn: number } }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'TOKEN_REFRESH'; payload: { accessToken: string; expiresIn: number } }
  | { type: 'SET_DEMO_MODE'; payload: boolean };

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  accessToken: null,
  refreshToken: null,
  tokenExpiresAt: null,
  isLoading: false,
  error: null,
  demoMode: process.env.REACT_APP_DEMO_MODE === 'true',
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'AUTH_SUCCESS':
      const expiresAt = new Date(Date.now() + action.payload.expiresIn * 1000);
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken,
        tokenExpiresAt: expiresAt,
        isLoading: false,
        error: null,
      };
    case 'AUTH_FAILURE':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        accessToken: null,
        refreshToken: null,
        tokenExpiresAt: null,
        isLoading: false,
        error: action.payload,
      };
    case 'LOGOUT':
      return {
        ...initialState,
        demoMode: state.demoMode,
      };
    case 'TOKEN_REFRESH':
      const newExpiresAt = new Date(Date.now() + action.payload.expiresIn * 1000);
      return {
        ...state,
        accessToken: action.payload.accessToken,
        tokenExpiresAt: newExpiresAt,
        error: null,
      };
    case 'SET_DEMO_MODE':
      return {
        ...state,
        demoMode: action.payload,
      };
    default:
      return state;
  }
}

interface AuthContextValue extends AuthState {
  login: () => Promise<void>;
  logout: () => void;
  handleOAuthCallback: (code: string, state: string) => Promise<void>;
  refreshToken: () => Promise<boolean>;
  setDemoMode: (enabled: boolean) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Secure token storage utilities
  const storeTokens = useCallback((accessToken: string, refreshToken: string) => {
    // In production, use httpOnly cookies or secure storage
    sessionStorage.setItem('access_token', accessToken);
    sessionStorage.setItem('refresh_token', refreshToken);
    
    // Update API client with new token
    apiClient.setAuthToken(accessToken);
  }, []);

  const clearTokens = useCallback(() => {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    apiClient.clearAuthToken();
  }, []);

  const login = useCallback(async () => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      // Initiate OAuth flow
      const response = await apiClient.initiateOAuth();
      
      // Redirect to Schwab OAuth page
      window.location.href = response.authorization_url;
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
    }
  }, []);

  const handleOAuthCallback = useCallback(async (code: string, state: string) => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      // Complete OAuth flow
      const response = await apiClient.completeOAuth(code, state);
      
      // Store tokens securely
      storeTokens(response.access_token, response.refresh_token);
      
      // Update auth state
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: response.user_info,
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
          expiresIn: response.expires_in,
        },
      });
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'OAuth callback failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      clearTokens();
    }
  }, [storeTokens, clearTokens]);

  const refreshTokenFn = useCallback(async (): Promise<boolean> => {
    try {
      if (!state.refreshToken) {
        return false;
      }
      
      const response = await apiClient.refreshToken();
      
      // Store new tokens
      storeTokens(response.access_token, response.refresh_token);
      
      // Update auth state
      dispatch({
        type: 'TOKEN_REFRESH',
        payload: {
          accessToken: response.access_token,
          expiresIn: response.expires_in,
        },
      });
      
      return true;
      
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      return false;
    }
  }, [state.refreshToken, storeTokens]);

  const logout = useCallback(() => {
    clearTokens();
    dispatch({ type: 'LOGOUT' });
  }, [clearTokens]);

  const setDemoMode = useCallback((enabled: boolean) => {
    dispatch({ type: 'SET_DEMO_MODE', payload: enabled });
  }, []);

  // Auto token refresh
  useEffect(() => {
    if (!state.isAuthenticated || !state.tokenExpiresAt) {
      return;
    }

    const refreshBuffer = 5 * 60 * 1000; // 5 minutes before expiry
    const refreshTime = state.tokenExpiresAt.getTime() - Date.now() - refreshBuffer;

    if (refreshTime > 0) {
      const timeout = setTimeout(() => {
        refreshTokenFn();
      }, refreshTime);

      return () => clearTimeout(timeout);
    } else {
      // Token already expired or about to expire
      refreshTokenFn();
    }
  }, [state.isAuthenticated, state.tokenExpiresAt, refreshTokenFn]);

  // Initialize from stored tokens on app start
  useEffect(() => {
    const storedAccessToken = sessionStorage.getItem('access_token');
    const storedRefreshToken = sessionStorage.getItem('refresh_token');

    if (storedAccessToken && storedRefreshToken) {
      // Validate stored token and restore auth state
      apiClient.setAuthToken(storedAccessToken);
      
      // Check auth status with backend
      apiClient.getAuthStatus()
        .then((status) => {
          if (status.is_authenticated) {
            // Token is valid, restore auth state
            // Note: This is simplified - in production, decode JWT or call user info endpoint
          } else {
            // Token invalid, clear stored tokens
            clearTokens();
          }
        })
        .catch(() => {
          clearTokens();
        });
    }
  }, [clearTokens]);

  const contextValue: AuthContextValue = {
    ...state,
    login,
    logout,
    handleOAuthCallback,
    refreshToken: refreshTokenFn,
    setDemoMode,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

#### 2. Authentication Components
```typescript
// src/frontend/src/components/Auth/AuthenticationPanel.tsx

import React, { useEffect } from 'react';
import { 
  Paper, 
  Typography, 
  Button, 
  Box, 
  Alert, 
  Chip,
  Switch,
  FormControlLabel,
  CircularProgress
} from '@mui/material';
import { AccountCircle, VpnKey, Cancel } from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';

export const AuthenticationPanel: React.FC = () => {
  const { 
    isAuthenticated, 
    user, 
    isLoading, 
    error, 
    demoMode,
    login, 
    logout,
    setDemoMode 
  } = useAuth();

  // Handle OAuth callback from URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');

    if (code && state) {
      handleOAuthCallback(code, state);
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  if (isLoading) {
    return (
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="center">
          <CircularProgress size={24} sx={{ mr: 2 }} />
          <Typography>Authenticating...</Typography>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper elevation={2} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <VpnKey sx={{ mr: 1 }} />
        Authentication Status
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Demo Mode Toggle */}
      <FormControlLabel
        control={
          <Switch
            checked={demoMode}
            onChange={(e) => setDemoMode(e.target.checked)}
            disabled={isAuthenticated}
          />
        }
        label="Demo Mode (Uses mock data)"
        sx={{ mb: 2 }}
      />

      {/* Authentication Status */}
      {isAuthenticated ? (
        <Box>
          <Box display="flex" alignItems="center" mb={2}>
            <AccountCircle color="success" sx={{ mr: 1 }} />
            <Chip label="Authenticated" color="success" />
          </Box>
          
          {user && (
            <Box mb={2}>
              <Typography variant="body2" gutterBottom>
                <strong>Name:</strong> {user.name || 'N/A'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Account:</strong> {user.accountType || 'N/A'}
              </Typography>
            </Box>
          )}

          <Button
            variant="contained"
            color="error"
            startIcon={<Cancel />}
            onClick={logout}
            size="small"
          >
            Logout
          </Button>
        </Box>
      ) : (
        <Box>
          <Box display="flex" alignItems="center" mb={2}>
            <Cancel color="error" sx={{ mr: 1 }} />
            <Chip 
              label={demoMode ? "Demo Mode" : "Not Authenticated"} 
              color={demoMode ? "warning" : "error"} 
            />
          </Box>

          {!demoMode && (
            <>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Connect your Schwab account to access live market data and execute trades.
              </Typography>
              
              <Button
                variant="contained"
                color="primary"
                startIcon={<VpnKey />}
                onClick={login}
                size="small"
              >
                Connect Schwab Account
              </Button>
            </>
          )}
          
          {demoMode && (
            <Typography variant="body2" color="text.secondary">
              Demo mode is enabled. You can explore all features with simulated data.
            </Typography>
          )}
        </Box>
      )}
    </Paper>
  );
};
```

#### 3. OAuth Callback Handler
```typescript
// src/frontend/src/components/Auth/OAuthCallback.tsx

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert } from '@mui/material';
import { useAuth } from '../../context/AuthContext';

export const OAuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const { handleOAuthCallback } = useAuth();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    const processOAuthCallback = async () => {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');

        if (error) {
          throw new Error(`OAuth error: ${error}`);
        }

        if (!code || !state) {
          throw new Error('Missing authorization code or state parameter');
        }

        await handleOAuthCallback(code, state);
        setStatus('success');
        
        // Redirect to dashboard after successful authentication
        setTimeout(() => {
          navigate('/dashboard');
        }, 2000);

      } catch (error) {
        console.error('OAuth callback error:', error);
        setErrorMessage(error instanceof Error ? error.message : 'Authentication failed');
        setStatus('error');
        
        // Redirect to login page after error
        setTimeout(() => {
          navigate('/');
        }, 5000);
      }
    };

    processOAuthCallback();
  }, [handleOAuthCallback, navigate]);

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      p={3}
    >
      {status === 'processing' && (
        <>
          <CircularProgress size={48} sx={{ mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Completing Authentication...
          </Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Please wait while we securely connect your Schwab account.
          </Typography>
        </>
      )}

      {status === 'success' && (
        <>
          <Typography variant="h6" color="success.main" gutterBottom>
            Authentication Successful!
          </Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Redirecting to dashboard...
          </Typography>
        </>
      )}

      {status === 'error' && (
        <Alert severity="error" sx={{ maxWidth: 400 }}>
          <Typography variant="body1" gutterBottom>
            Authentication Failed
          </Typography>
          <Typography variant="body2">
            {errorMessage}
          </Typography>
          <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
            Redirecting to home page...
          </Typography>
        </Alert>
      )}
    </Box>
  );
};
```

## Implementation Tasks

### Task 1: Backend OAuth Service (Days 1-2)
1. **Complete OAuth Flow Implementation**
   - Implement SchwabOAuthService with full OAuth2 flow
   - Add secure state parameter validation
   - Implement token exchange and refresh mechanisms

2. **Enhanced API Routes**
   - Add OAuth initiation and completion endpoints
   - Implement token refresh and status endpoints
   - Add proper error handling and logging

### Task 2: Frontend Authentication System (Days 3-4)
1. **Authentication Context Implementation**
   - Create comprehensive auth context with state management
   - Implement secure token storage and management
   - Add automatic token refresh logic

2. **Authentication Components**
   - Build AuthenticationPanel for status display and controls
   - Create OAuthCallback component for handling OAuth redirects
   - Add demo mode toggle and user info display

### Task 3: Secure API Integration (Days 5-6)
1. **API Client Enhancement**
   - Add automatic token injection for authenticated requests
   - Implement token refresh on API call failures
   - Add authentication error handling

2. **Authenticated Analytics**
   - Test all analytics endpoints with authenticated requests
   - Verify WebSocket authentication for real-time data
   - Ensure graceful fallback to demo mode when needed

## Phase 4 Dependencies

### Requires from Phase 3
- [x] Reliable WebSocket infrastructure
- [x] Complete analytics dashboard functional
- [x] Real-time data streaming working

### Phase 4 Completes Extension
- Production-ready Schwab OAuth integration
- Secure token management and automatic refresh
- Complete end-to-end authenticated analytics workflow

## Testing Requirements

### Backend OAuth Tests
```python
def test_oauth_flow_initiation():
    oauth_service = SchwabOAuthService()
    result = await oauth_service.initiate_oauth_flow()
    
    assert "authorization_url" in result
    assert "state" in result
    assert result["state"] in oauth_service._oauth_states

def test_oauth_completion():
    # Mock successful token exchange
    oauth_service = SchwabOAuthService()
    # Test completion flow with valid code and state
```

### Frontend Authentication Tests
```typescript
describe('AuthContext', () => {
  test('handles OAuth callback successfully', async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await act(async () => {
      await result.current.handleOAuthCallback('test-code', 'test-state');
    });

    expect(result.current.isAuthenticated).toBe(true);
  });

  test('handles token refresh automatically', async () => {
    // Test automatic token refresh logic
  });
});
```

## Phase 4 Completion Criteria

### Functional Completion
- [ ] Complete Schwab OAuth flow functional from frontend to backend
- [ ] Authentication status properly displayed with user information
- [ ] Token refresh handled automatically without user intervention
- [ ] Authentication errors provide clear guidance for resolution
- [ ] Demo mode preserves full functionality for development/testing

### Security Validation
- [ ] OAuth state parameter validation prevents CSRF attacks
- [ ] Tokens stored securely (httpOnly cookies in production)
- [ ] Automatic token refresh prevents expired token issues
- [ ] Error handling doesn't leak sensitive information

### Production Readiness
- [ ] All analytics endpoints work with authenticated requests
- [ ] WebSocket authentication integrated for real-time data
- [ ] Graceful degradation when authentication fails
- [ ] Complete end-to-end user workflow tested

**Phase 4 Success Metric**: Production-ready Schwab OAuth integration + Complete authenticated analytics workflow + Security best practices implemented + Demo mode preserved for development