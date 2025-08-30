// Simple notification service stub
export interface NotificationService {
  showAlert: (message: string) => void;
  playSound: (soundType: string) => void;
}

class SimpleNotificationService implements NotificationService {
  showAlert(message: string) {
    // Simple browser alert for now
    alert(message);
  }

  playSound(soundType: string) {
    // No sound implementation for now
    console.log(`Playing sound: ${soundType}`);
  }
}

export const notificationService = new SimpleNotificationService();
export default notificationService;