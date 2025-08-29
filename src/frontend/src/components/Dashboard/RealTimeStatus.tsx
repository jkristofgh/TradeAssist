/**
 * RealTimeStatus Component
 * 
 * Displays real-time connection status, WebSocket health, and basic system metrics
 */

import React from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';

interface RealTimeStatusProps {
  className?: string;
}

const RealTimeStatus: React.FC<RealTimeStatusProps> = ({ className = '' }) => {
  const { isConnected, reconnectAttempts, error } = useWebSocket();

  return (
    <div className={`realtime-status ${className}`}>
      <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
        <div className="indicator-dot" />
        <span className="status-text">
          {isConnected ? 'Live Data' : 'Offline'}
        </span>
      </div>
      
      {!isConnected && reconnectAttempts > 0 && (
        <div className="reconnect-info">
          Reconnecting... (attempt {reconnectAttempts})
        </div>
      )}
      
      {error && (
        <div className="error-info" title={error}>
          Connection Error
        </div>
      )}
    </div>
  );
};

export default RealTimeStatus;