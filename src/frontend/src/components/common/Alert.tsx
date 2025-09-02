import React from 'react';
import './Alert.css';

export interface AlertProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'destructive';
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({ children, variant = 'default', className = '' }) => {
  return (
    <div className={`alert alert-${variant} ${className}`}>
      {children}
    </div>
  );
};

export interface AlertDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export const AlertDescription: React.FC<AlertDescriptionProps> = ({ children, className = '' }) => {
  return <div className={`alert-description ${className}`}>{children}</div>;
};