/**
 * Authentication Panel Component (Simplified)
 * 
 * Provides authentication status display, OAuth flow controls, and demo mode toggle
 * without external UI library dependencies.
 */

import React from 'react';
import { useAuth } from '../../context/AuthContext';
import './AuthenticationPanel.css';

export const AuthenticationPanel: React.FC = () => {
  const { 
    isAuthenticated, 
    user, 
    demoMode, 
    connectionStatus, 
    isLoading, 
    error, 
    login, 
    logout, 
    setDemoMode, 
    clearError 
  } = useAuth();

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return '#4caf50';
      case 'connecting':
        return '#ff9800';
      case 'disconnected':
      case 'not_authenticated':
        return '#f44336';
      default:
        return '#9e9e9e';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'disconnected':
        return 'Disconnected';
      case 'not_authenticated':
        return 'Not Authenticated';
      case 'token_expired':
        return 'Token Expired';
      case 'token_invalid':
        return 'Token Invalid';
      default:
        return 'Unknown';
    }
  };

  const handleDemoModeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDemoMode(e.target.checked);
  };

  const handleLogin = async () => {
    clearError();
    await login();
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="auth-panel">
      <div className="auth-header">
        <h2>Authentication Status</h2>
        <div className="connection-status">
          <span 
            className="status-indicator" 
            style={{ backgroundColor: getConnectionStatusColor() }}
          ></span>
          <span className="status-text">{getConnectionStatusText()}</span>
        </div>
      </div>

      {error && (
        <div className="error-alert">
          <div className="error-content">
            <strong>Authentication Error:</strong>
            <p>{error}</p>
            <button onClick={clearError} className="btn-clear-error">
              Dismiss
            </button>
          </div>
        </div>
      )}

      <div className="auth-content">
        {!isAuthenticated ? (
          <div className="unauthenticated-state">
            <div className="status-info">
              <h3>Not Authenticated</h3>
              <p>Connect your Schwab account to access live market data and trading features.</p>
            </div>

            <div className="demo-mode-section">
              <label className="demo-mode-toggle">
                <input
                  type="checkbox"
                  checked={demoMode}
                  onChange={handleDemoModeChange}
                  disabled={isAuthenticated && !demoMode}
                />
                <span className="toggle-text">Demo Mode</span>
              </label>
              {demoMode && (
                <p className="demo-notice">
                  Demo mode enabled. Using simulated data for testing.
                </p>
              )}
            </div>

            <button 
              onClick={handleLogin} 
              disabled={isLoading}
              className="btn-primary btn-login"
            >
              {isLoading ? 'Connecting...' : 'Connect Schwab Account'}
            </button>
          </div>
        ) : (
          <div className="authenticated-state">
            <div className="user-info">
              <h3>Connected Successfully</h3>
              {user && (
                <div className="user-details">
                  <p><strong>Name:</strong> {user.name || user.id}</p>
                  {user.email && <p><strong>Email:</strong> {user.email}</p>}
                  {user.accountType && <p><strong>Account:</strong> {user.accountType}</p>}
                </div>
              )}
            </div>

            {demoMode && (
              <div className="demo-indicator">
                <span className="demo-badge">DEMO MODE</span>
                <p>Using simulated data for testing</p>
              </div>
            )}

            <div className="auth-actions">
              <button 
                onClick={handleLogout}
                className="btn-secondary btn-logout"
              >
                Disconnect
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};