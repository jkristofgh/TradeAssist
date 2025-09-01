/**
 * Error Alert Component
 * 
 * Reusable error display component with retry functionality
 */

import React from 'react';
import './ErrorAlert.css';

interface ErrorAlertProps {
  message: string;
  error?: any;
  onRetry?: () => void;
  className?: string;
  showDetails?: boolean;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  message,
  error,
  onRetry,
  className = '',
  showDetails = false
}) => {
  const getErrorDetails = () => {
    if (!error) return '';
    
    if (error instanceof Error) {
      return error.message;
    }
    
    if (typeof error === 'object' && error.message) {
      return error.message;
    }
    
    if (typeof error === 'string') {
      return error;
    }
    
    return 'Unknown error occurred';
  };

  return (
    <div className={`error-alert ${className}`}>
      <div className="error-alert__icon">⚠️</div>
      <div className="error-alert__content">
        <div className="error-alert__message">{message}</div>
        {showDetails && error && (
          <div className="error-alert__details">{getErrorDetails()}</div>
        )}
        {onRetry && (
          <button 
            className="error-alert__retry-button"
            onClick={onRetry}
            type="button"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  );
};