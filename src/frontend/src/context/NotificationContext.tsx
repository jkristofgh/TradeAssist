import React, { createContext, useContext, ReactNode } from 'react';

// Simple notification context stub
interface NotificationContextType {
  showNotification: (message: string, type?: string) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const showNotification = (message: string, type = 'info') => {
    console.log(`Notification (${type}): ${message}`);
    // Simple alert for now
    if (type === 'error') {
      alert(`Error: ${message}`);
    }
  };

  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
    </NotificationContext.Provider>
  );
};