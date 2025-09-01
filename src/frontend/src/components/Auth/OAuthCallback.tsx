/**
 * OAuth Callback Handler Component (Simplified)
 * 
 * Handles the OAuth callback from Schwab, processes the authorization code,
 * and manages the authentication completion flow with user feedback.
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './OAuthCallback.css';

interface ProcessingStep {
  label: string;
  description: string;
  completed: boolean;
  error?: string;
}

export const OAuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const { handleOAuthCallback, isAuthenticated, error, user } = useAuth();
  
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [steps, setSteps] = useState<ProcessingStep[]>([
    {
      label: 'Validating Authorization',
      description: 'Checking authorization code and state parameters',
      completed: false
    },
    {
      label: 'Exchanging Tokens',
      description: 'Exchanging authorization code for access tokens',
      completed: false
    },
    {
      label: 'Retrieving User Info',
      description: 'Fetching user account information from Schwab',
      completed: false
    },
    {
      label: 'Finalizing Authentication',
      description: 'Completing authentication setup',
      completed: false
    }
  ]);
  
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const processOAuthCallback = async () => {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');
        const errorDescription = urlParams.get('error_description');

        // Step 1: Validate parameters
        setActiveStep(0);
        await new Promise(resolve => setTimeout(resolve, 500)); // Brief delay for UX

        if (error) {
          const errorMsg = `OAuth error: ${error}${errorDescription ? ` - ${errorDescription}` : ''}`;
          throw new Error(errorMsg);
        }

        if (!code || !state) {
          throw new Error('Missing authorization code or state parameter. The OAuth flow may have been interrupted.');
        }

        setSteps(prev => prev.map((step, index) => 
          index === 0 ? { ...step, completed: true } : step
        ));

        // Step 2: Exchange tokens
        setActiveStep(1);
        await new Promise(resolve => setTimeout(resolve, 300));
        
        await handleOAuthCallback(code, state);
        
        setSteps(prev => prev.map((step, index) => 
          index <= 2 ? { ...step, completed: true } : step
        ));

        // Step 3: Finalize
        setActiveStep(3);
        await new Promise(resolve => setTimeout(resolve, 300));
        
        setSteps(prev => prev.map(step => ({ ...step, completed: true })));
        setStatus('success');
        
        console.log('OAuth callback processing completed successfully');
        
        // Redirect to dashboard after successful authentication
        setTimeout(() => {
          navigate('/');
        }, 2500);

      } catch (error: any) {
        console.error('OAuth callback error:', error);
        
        const errorMsg = error instanceof Error ? error.message : 'Authentication failed';
        setErrorMessage(errorMsg);
        setStatus('error');
        
        // Update current step with error
        setSteps(prev => prev.map((step, index) => 
          index === activeStep 
            ? { ...step, error: errorMsg, completed: false }
            : step
        ));
        
        // Redirect to home page after error
        setTimeout(() => {
          navigate('/');
        }, 8000);
      }
    };

    processOAuthCallback();
  }, [handleOAuthCallback, navigate, activeStep]);

  // Handle successful authentication state change
  useEffect(() => {
    if (isAuthenticated && user) {
      setStatus('success');
    }
  }, [isAuthenticated, user]);

  // Handle authentication errors
  useEffect(() => {
    if (error) {
      setErrorMessage(error);
      setStatus('error');
    }
  }, [error]);

  const handleReturnHome = () => {
    navigate('/');
  };

  return (
    <div className="oauth-callback">
      <div className="callback-container">
        {status === 'processing' && (
          <>
            <div className="callback-header">
              <div className="security-icon">🔐</div>
              <div>
                <h2>Completing Authentication</h2>
                <p>Securely connecting your Schwab account...</p>
              </div>
            </div>

            <div className="progress-steps">
              {steps.map((step, index) => (
                <div key={index} className={`progress-step ${
                  step.completed ? 'completed' : 
                  step.error ? 'error' : 
                  index === activeStep ? 'active' : 'pending'
                }`}>
                  <div className="step-indicator">
                    {step.completed ? '✓' : 
                     step.error ? '✗' : 
                     index === activeStep ? '⟳' : (index + 1)}
                  </div>
                  <div className="step-content">
                    <div className="step-label">{step.label}</div>
                    <div className="step-description">
                      {step.error || step.description}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="processing-note">
              <p>This process should complete in a few seconds.</p>
              <p>Please do not close this page.</p>
            </div>
          </>
        )}

        {status === 'success' && (
          <div className="success-state">
            <div className="success-icon">✅</div>
            
            <h2>Authentication Successful!</h2>
            
            {user && (
              <div className="user-welcome">
                <p>Welcome back, <strong>{user.name || user.id}</strong></p>
                {user.accountType && (
                  <p className="account-type">Account: {user.accountType}</p>
                )}
              </div>
            )}
            
            <div className="redirect-info">
              <div className="spinner">⟳</div>
              <p>Redirecting to dashboard...</p>
            </div>

            <button
              className="btn-home"
              onClick={handleReturnHome}
            >
              Go to Dashboard Now
            </button>
          </div>
        )}

        {status === 'error' && (
          <div className="error-state">
            <div className="error-icon">❌</div>
            
            <h2>Authentication Failed</h2>
            
            <div className="error-details">
              <p><strong>Error Details:</strong></p>
              <p>{errorMessage}</p>
            </div>

            <div className="recovery-suggestions">
              <p><strong>What you can do:</strong></p>
              <ul>
                <li>Try the authentication process again</li>
                <li>Check your Schwab API credentials configuration</li>
                <li>Use Demo Mode to explore the application</li>
                <li>Contact support if the problem persists</li>
              </ul>
            </div>

            <button
              className="btn-home"
              onClick={handleReturnHome}
            >
              Return to Home
            </button>

            <p className="auto-redirect">
              Redirecting automatically in a few seconds...
            </p>
          </div>
        )}
      </div>
    </div>
  );
};