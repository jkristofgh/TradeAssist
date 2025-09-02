/**
 * Authentication Context Provider
 * 
 * Provides comprehensive OAuth2 authentication state management with 
 * automatic token refresh, secure storage, and demo mode support.
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { apiClient } from '../services/apiClient';

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

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
  connectionStatus: string;
}

type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; accessToken: string; refreshToken: string; expiresIn: number; demoMode: boolean } }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'TOKEN_REFRESH'; payload: { accessToken: string; expiresIn: number } }
  | { type: 'SET_DEMO_MODE'; payload: boolean }
  | { type: 'SET_CONNECTION_STATUS'; payload: string }
  | { type: 'CLEAR_ERROR' };

// =============================================================================
// REDUCER
// =============================================================================

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  accessToken: null,
  refreshToken: null,
  tokenExpiresAt: null,
  isLoading: false,
  error: null,
  demoMode: process.env.REACT_APP_DEMO_MODE === 'true',
  connectionStatus: 'disconnected',
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
        demoMode: action.payload.demoMode,
        connectionStatus: 'connected',
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
        connectionStatus: 'error',
      };
    
    case 'LOGOUT':
      return {
        ...initialState,
        demoMode: state.demoMode,
        connectionStatus: 'disconnected',
      };
    
    case 'TOKEN_REFRESH':
      const newExpiresAt = new Date(Date.now() + action.payload.expiresIn * 1000);
      return {
        ...state,
        accessToken: action.payload.accessToken,
        tokenExpiresAt: newExpiresAt,
        error: null,
        connectionStatus: 'connected',
      };
    
    case 'SET_DEMO_MODE':
      return {
        ...state,
        demoMode: action.payload,
        // If enabling demo mode, set demo authentication
        isAuthenticated: action.payload,
        user: action.payload ? {
          id: 'demo_user',
          name: 'Demo User',
          email: 'demo@tradeassist.local',
          accountType: 'Demo Account'
        } : null,
        connectionStatus: action.payload ? 'connected' : 'disconnected',
      };
    
    case 'SET_CONNECTION_STATUS':
      return {
        ...state,
        connectionStatus: action.payload,
      };
    
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    
    default:
      return state;
  }
}

// =============================================================================
// CONTEXT DEFINITION
// =============================================================================

interface AuthContextValue extends AuthState {
  login: () => Promise<void>;
  logout: () => void;
  handleOAuthCallback: (code: string, state: string) => Promise<void>;
  refreshAuthToken: () => Promise<boolean>;
  setDemoMode: (enabled: boolean) => void;
  clearError: () => void;
  checkAuthStatus: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// =============================================================================
// PROVIDER COMPONENT
// =============================================================================

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // =============================================================================
  // TOKEN STORAGE UTILITIES
  // =============================================================================

  const storeTokens = useCallback((accessToken: string, refreshToken: string) => {
    // In production, use httpOnly cookies or secure storage
    // For now, using sessionStorage with awareness of security implications
    try {
      sessionStorage.setItem('access_token', accessToken);
      sessionStorage.setItem('refresh_token', refreshToken);
      
      // Update API client with new token
      apiClient.setAuthToken(accessToken);
      
      console.log('Tokens stored successfully');
    } catch (error) {
      console.error('Failed to store tokens:', error);
    }
  }, []);

  const clearTokens = useCallback(() => {
    try {
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('refresh_token');
      apiClient.clearAuthToken();
      
      console.log('Tokens cleared successfully');
    } catch (error) {
      console.error('Failed to clear tokens:', error);
    }
  }, []);

  const getStoredTokens = useCallback(() => {
    try {
      return {
        accessToken: sessionStorage.getItem('access_token'),
        refreshToken: sessionStorage.getItem('refresh_token'),
      };
    } catch (error) {
      console.error('Failed to get stored tokens:', error);
      return { accessToken: null, refreshToken: null };
    }
  }, []);

  // =============================================================================
  // AUTHENTICATION OPERATIONS
  // =============================================================================

  const login = useCallback(async () => {
    try {
      dispatch({ type: 'AUTH_START' });
      dispatch({ type: 'CLEAR_ERROR' });
      
      console.log('Initiating OAuth login flow');
      
      // Initiate OAuth flow
      const response = await apiClient.initiateOAuth();
      
      if (response.demoMode) {
        // Handle demo mode authentication
        console.log('Demo mode authentication initiated');
        dispatch({
          type: 'AUTH_SUCCESS',
          payload: {
            user: {
              id: 'demo_user',
              name: 'Demo User',
              email: 'demo@tradeassist.local',
              accountType: 'Demo Account'
            },
            accessToken: 'demo_token',
            refreshToken: 'demo_refresh_token',
            expiresIn: 3600,
            demoMode: true
          }
        });
        return;
      }
      
      // Redirect to Schwab OAuth page
      console.log('Redirecting to Schwab OAuth page');
      window.location.href = response.authorizationUrl;
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      console.error('Login failed:', errorMessage);
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
    }
  }, []);

  const handleOAuthCallback = useCallback(async (code: string, state: string) => {
    try {
      dispatch({ type: 'AUTH_START' });
      dispatch({ type: 'CLEAR_ERROR' });
      
      console.log('Processing OAuth callback', { codeLength: code.length, state });
      
      // Complete OAuth flow
      const response = await apiClient.completeOAuth(code, state);
      
      // Store tokens securely
      if (!response.demoMode) {
        storeTokens(response.accessToken, response.refreshToken || '');
      }
      
      // Update auth state
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: response.userInfo,
          accessToken: response.accessToken,
          refreshToken: response.refreshToken || '',
          expiresIn: response.expiresIn,
          demoMode: response.demoMode
        },
      });
      
      console.log('OAuth callback processed successfully');
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'OAuth callback failed';
      console.error('OAuth callback failed:', errorMessage);
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      clearTokens();
    }
  }, [storeTokens, clearTokens]);

  const refreshAuthTokenFn = useCallback(async (): Promise<boolean> => {
    try {
      const { refreshToken } = getStoredTokens();
      
      if (!refreshToken) {
        console.warn('No refresh token available');
        return false;
      }
      
      if (state.demoMode || refreshToken.startsWith('demo_')) {
        // Handle demo mode refresh
        console.log('Demo mode token refresh');
        dispatch({
          type: 'TOKEN_REFRESH',
          payload: {
            accessToken: 'demo_access_token_' + Math.random().toString(36),
            expiresIn: 3600,
          },
        });
        return true;
      }
      
      console.log('Refreshing access token');
      const response = await apiClient.refreshToken(refreshToken);
      
      // Store new tokens
      storeTokens(response.accessToken, response.refreshToken || refreshToken);
      
      // Update auth state
      dispatch({
        type: 'TOKEN_REFRESH',
        payload: {
          accessToken: response.accessToken,
          expiresIn: response.expiresIn,
        },
      });
      
      console.log('Token refreshed successfully');
      return true;
      
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      return false;
    }
  }, [getStoredTokens, storeTokens, state.demoMode]);

  const logout = useCallback(() => {
    console.log('Logging out user');
    clearTokens();
    dispatch({ type: 'LOGOUT' });
    
    // Call logout endpoint to clean up server-side state
    apiClient.logout().catch(error => {
      console.warn('Server-side logout failed:', error);
    });
  }, [clearTokens]);

  const setDemoMode = useCallback((enabled: boolean) => {
    console.log('Setting demo mode:', enabled);
    dispatch({ type: 'SET_DEMO_MODE', payload: enabled });
    
    if (enabled) {
      // Set demo mode in API client
      apiClient.setDemoMode(true);
    } else {
      apiClient.setDemoMode(false);
      // Clear any demo tokens
      clearTokens();
    }
  }, [clearTokens]);

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  const checkAuthStatus = useCallback(async () => {
    try {
      console.log('Checking authentication status');
      const status = await apiClient.getAuthStatus();
      
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: status.connectionStatus });
      
      if (status.demoMode) {
        dispatch({ type: 'SET_DEMO_MODE', payload: true });
      }
      
      if (status.isAuthenticated && status.userInfo) {
        // Restore authentication state
        dispatch({
          type: 'AUTH_SUCCESS',
          payload: {
            user: status.userInfo,
            accessToken: getStoredTokens().accessToken || 'demo_token',
            refreshToken: getStoredTokens().refreshToken || 'demo_refresh_token',
            expiresIn: status.tokenExpiresAt ? 
              Math.max(0, (new Date(status.tokenExpiresAt).getTime() - Date.now()) / 1000) : 3600,
            demoMode: status.demoMode
          }
        });
      }
      
    } catch (error) {
      console.warn('Auth status check failed:', error);
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: 'error' });
    }
  }, [getStoredTokens]);

  // =============================================================================
  // AUTO TOKEN REFRESH
  // =============================================================================

  useEffect(() => {
    if (!state.isAuthenticated || !state.tokenExpiresAt || state.demoMode) {
      return;
    }

    const refreshBuffer = 5 * 60 * 1000; // 5 minutes before expiry
    const refreshTime = state.tokenExpiresAt.getTime() - Date.now() - refreshBuffer;

    if (refreshTime > 0) {
      const timeout = setTimeout(() => {
        console.log('Auto-refreshing token');
        refreshAuthTokenFn();
      }, refreshTime);

      return () => clearTimeout(timeout);
    } else {
      // Token already expired or about to expire
      console.log('Token expired, attempting refresh');
      refreshAuthTokenFn();
    }
  }, [state.isAuthenticated, state.tokenExpiresAt, state.demoMode, refreshAuthTokenFn]);

  // =============================================================================
  // INITIALIZATION
  // =============================================================================

  useEffect(() => {
    const initializeAuth = async () => {
      const { accessToken, refreshToken } = getStoredTokens();

      if (accessToken && refreshToken) {
        console.log('Found stored tokens, validating...');
        
        // Set token in API client
        apiClient.setAuthToken(accessToken);
        
        // Check auth status with backend
        await checkAuthStatus();
      } else {
        // No stored tokens, check for demo mode
        await checkAuthStatus();
      }
    };

    initializeAuth();
  }, [getStoredTokens, checkAuthStatus]);

  // =============================================================================
  // CONTEXT VALUE
  // =============================================================================

  const contextValue: AuthContextValue = {
    ...state,
    login,
    logout,
    handleOAuthCallback,
    refreshAuthToken: refreshAuthTokenFn,
    setDemoMode,
    clearError,
    checkAuthStatus,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// =============================================================================
// CUSTOM HOOK
// =============================================================================

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};