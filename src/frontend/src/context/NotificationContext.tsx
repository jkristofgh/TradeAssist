/**
 * Notification Context
 * 
 * React context for managing notification state and preferences across the application.
 * Provides hooks for accessing notification service and handling real-time alert delivery.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { ToastContainer } from 'react-toastify';
import { 
  notificationService, 
  NotificationPreferences, 
  NotificationResult 
} from '../services/notificationService';
import { AlertFiredMessage } from '../types';
import { useWebSocket } from '../hooks/useWebSocket';

// =============================================================================
// TYPES
// =============================================================================

interface NotificationContextValue {
  preferences: NotificationPreferences;
  updatePreferences: (updates: Partial<NotificationPreferences>) => void;
  testNotification: (channel: keyof NotificationPreferences) => void;
  clearAllNotifications: () => void;
  deliveryHistory: NotificationResult[];
  isConnected: boolean;
}

interface NotificationProviderProps {
  children: ReactNode;
}

// =============================================================================
// CONTEXT CREATION
// =============================================================================

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

// =============================================================================
// PROVIDER COMPONENT
// =============================================================================

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [preferences, setPreferences] = useState<NotificationPreferences>(\n    () => notificationService.getPreferences()\n  );\n  const [deliveryHistory, setDeliveryHistory] = useState<NotificationResult[]>([]);\n  const [isConnected, setIsConnected] = useState(false);\n\n  // WebSocket integration for real-time alerts\n  const { socket, isConnected: wsConnected } = useWebSocket(\n    process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/realtime'\n  );\n\n  // Update connection status\n  useEffect(() => {\n    setIsConnected(wsConnected);\n  }, [wsConnected]);\n\n  // Handle incoming alert messages\n  useEffect(() => {\n    if (!socket) return;\n\n    const handleMessage = async (event: MessageEvent) => {\n      try {\n        const message = JSON.parse(event.data);\n        \n        if (message.type === 'alert_fired') {\n          const alertMessage = message as AlertFiredMessage;\n          \n          // Deliver notification through all enabled channels\n          const result = await notificationService.deliverAlert(alertMessage);\n          \n          // Add to delivery history\n          setDeliveryHistory(prev => {\n            const updated = [result, ...prev];\n            // Keep only last 100 deliveries\n            return updated.slice(0, 100);\n          });\n        }\n      } catch (error) {\n        console.error('Failed to process WebSocket message:', error);\n      }\n    };\n\n    socket.addEventListener('message', handleMessage);\n    \n    return () => {\n      socket.removeEventListener('message', handleMessage);\n    };\n  }, [socket]);\n\n  // Preference management\n  const updatePreferences = useCallback((updates: Partial<NotificationPreferences>) => {\n    const newPreferences = { ...preferences, ...updates };\n    setPreferences(newPreferences);\n    notificationService.updatePreferences(updates);\n  }, [preferences]);\n\n  // Test notification\n  const testNotification = useCallback((channel: keyof NotificationPreferences) => {\n    notificationService.testNotification(channel);\n  }, []);\n\n  // Clear all notifications\n  const clearAllNotifications = useCallback(() => {\n    notificationService.clearAllNotifications();\n  }, []);\n\n  // Context value\n  const contextValue: NotificationContextValue = {\n    preferences,\n    updatePreferences,\n    testNotification,\n    clearAllNotifications,\n    deliveryHistory,\n    isConnected\n  };\n\n  return (\n    <NotificationContext.Provider value={contextValue}>\n      {children}\n      \n      {/* Toast Container for in-app notifications */}\n      <ToastContainer\n        position={preferences.inApp.position}\n        autoClose={preferences.inApp.autoClose}\n        hideProgressBar={false}\n        newestOnTop={true}\n        closeOnClick\n        rtl={false}\n        pauseOnFocusLoss\n        draggable\n        pauseOnHover\n        theme=\"dark\"\n        className=\"toast-container\"\n        toastClassName=\"toast-item\"\n        bodyClassName=\"toast-body\"\n        progressClassName=\"toast-progress\"\n        limit={5} // Maximum 5 toasts at once\n      />\n    </NotificationContext.Provider>\n  );\n};\n\n// =============================================================================\n// CUSTOM HOOK\n// =============================================================================\n\nexport const useNotifications = (): NotificationContextValue => {\n  const context = useContext(NotificationContext);\n  \n  if (context === undefined) {\n    throw new Error('useNotifications must be used within a NotificationProvider');\n  }\n  \n  return context;\n};\n\n// =============================================================================\n// NOTIFICATION PREFERENCES HOOK\n// =============================================================================\n\nexport const useNotificationPreferences = () => {\n  const { preferences, updatePreferences, testNotification } = useNotifications();\n  \n  const updateInAppPreferences = useCallback((updates: Partial<NotificationPreferences['inApp']>) => {\n    updatePreferences({ inApp: { ...preferences.inApp, ...updates } });\n  }, [preferences.inApp, updatePreferences]);\n  \n  const updateSoundPreferences = useCallback((updates: Partial<NotificationPreferences['sound']>) => {\n    updatePreferences({ sound: { ...preferences.sound, ...updates } });\n  }, [preferences.sound, updatePreferences]);\n  \n  const updateSlackPreferences = useCallback((updates: Partial<NotificationPreferences['slack']>) => {\n    updatePreferences({ slack: { ...preferences.slack, ...updates } });\n  }, [preferences.slack, updatePreferences]);\n  \n  const updateEmailPreferences = useCallback((updates: Partial<NotificationPreferences['email']>) => {\n    updatePreferences({ email: { ...preferences.email, ...updates } });\n  }, [preferences.email, updatePreferences]);\n  \n  return {\n    preferences,\n    updateInAppPreferences,\n    updateSoundPreferences,\n    updateSlackPreferences,\n    updateEmailPreferences,\n    testNotification\n  };\n};\n\n// =============================================================================\n// DELIVERY HISTORY HOOK\n// =============================================================================\n\nexport const useNotificationHistory = () => {\n  const { deliveryHistory, isConnected } = useNotifications();\n  \n  const getDeliveryStats = useCallback(() => {\n    const total = deliveryHistory.length;\n    const successful = deliveryHistory.reduce((sum, result) => sum + result.successfulChannels, 0);\n    const totalChannels = deliveryHistory.reduce((sum, result) => sum + result.totalChannels, 0);\n    const successRate = totalChannels > 0 ? (successful / totalChannels) * 100 : 0;\n    \n    const channelStats = deliveryHistory.reduce((stats, result) => {\n      result.deliveryStatus.forEach(status => {\n        if (!stats[status.channel]) {\n          stats[status.channel] = { delivered: 0, failed: 0, total: 0 };\n        }\n        stats[status.channel].total++;\n        if (status.status === 'delivered') {\n          stats[status.channel].delivered++;\n        } else if (status.status === 'failed') {\n          stats[status.channel].failed++;\n        }\n      });\n      return stats;\n    }, {} as Record<string, { delivered: number; failed: number; total: number }>);\n    \n    return {\n      total,\n      successful,\n      totalChannels,\n      successRate,\n      channelStats\n    };\n  }, [deliveryHistory]);\n  \n  return {\n    deliveryHistory,\n    isConnected,\n    getDeliveryStats\n  };\n};