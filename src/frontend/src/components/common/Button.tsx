import React from 'react';
import './Button.css';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'outline' | 'ghost' | 'link' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({ 
  variant = 'default', 
  size = 'md', 
  className = '', 
  children, 
  ...props 
}) => {
  return (
    <button 
      className={`button button-${variant} button-${size} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};