// Enhanced notification service with toast-like functionality
export interface NotificationService {
  showAlert: (message: string) => void;
  playSound: (soundType: string) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  warning: (message: string) => void;
  info: (message: string) => void;
}

class SimpleNotificationService implements NotificationService {
  private notifications: Array<{ message: string; type: string; timestamp: number }> = [];

  showAlert(message: string) {
    // Simple browser alert for now
    alert(message);
  }

  playSound(soundType: string) {
    // No sound implementation for now
    console.log(`Playing sound: ${soundType}`);
  }

  success(message: string) {
    console.log(`✅ SUCCESS: ${message}`);
    this.addNotification(message, 'success');
  }

  error(message: string) {
    console.error(`❌ ERROR: ${message}`);
    this.addNotification(message, 'error');
  }

  warning(message: string) {
    console.warn(`⚠️ WARNING: ${message}`);
    this.addNotification(message, 'warning');
  }

  info(message: string) {
    console.info(`ℹ️ INFO: ${message}`);
    this.addNotification(message, 'info');
  }

  private addNotification(message: string, type: string) {
    this.notifications.push({ 
      message, 
      type, 
      timestamp: Date.now() 
    });
    // Keep only last 10 notifications
    if (this.notifications.length > 10) {
      this.notifications.shift();
    }
  }
}

export const notificationService = new SimpleNotificationService();
export default notificationService;