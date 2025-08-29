/**
 * Notification Service
 * 
 * Centralized notification handling for multi-channel delivery including
 * in-app toast messages, sound notifications, and external integrations.
 * Optimized for <100ms notification display and <200ms multi-channel delivery.
 */

import { toast, ToastPosition, ToastOptions, Id as ToastId } from 'react-toastify';
import { AlertFiredMessage, AlertLogWithDetails } from '../types';

// =============================================================================
// TYPES
// =============================================================================

export interface NotificationChannel {
  id: string;
  name: string;
  enabled: boolean;
  config: Record<string, any>;
}

export interface NotificationPreferences {
  inApp: {
    enabled: boolean;
    position: ToastPosition;
    autoClose: number;
    sound: boolean;
  };
  sound: {
    enabled: boolean;
    volume: number;
    alertTone: string;
  };
  slack: {
    enabled: boolean;
    webhookUrl?: string;
    channel?: string;
    username?: string;
  };
  email: {
    enabled: boolean;
    addresses: string[];
  };
}

export interface NotificationDeliveryStatus {
  channel: string;
  status: 'pending' | 'delivered' | 'failed';
  timestamp: string;
  error?: string;
}

export interface NotificationResult {
  id: string;
  alertId: number;
  deliveryStatus: NotificationDeliveryStatus[];
  totalChannels: number;
  successfulChannels: number;
}

// =============================================================================
// DEFAULT CONFIGURATION
// =============================================================================

const DEFAULT_PREFERENCES: NotificationPreferences = {
  inApp: {
    enabled: true,
    position: 'top-right',
    autoClose: 5000,
    sound: true
  },
  sound: {
    enabled: true,
    volume: 0.7,
    alertTone: 'default'
  },
  slack: {
    enabled: false
  },
  email: {
    enabled: false,
    addresses: []
  }
};

// Alert tone options
const ALERT_TONES: Record<string, string> = {
  default: '/sounds/alert-default.wav',
  chime: '/sounds/alert-chime.wav',
  beep: '/sounds/alert-beep.wav',
  bell: '/sounds/alert-bell.wav',
  notification: '/sounds/alert-notification.wav'
};

// =============================================================================
// NOTIFICATION SERVICE CLASS
// =============================================================================

export class NotificationService {
  private preferences: NotificationPreferences;
  private audioContext: AudioContext | null = null;
  private audioCache: Map<string, AudioBuffer> = new Map();
  private pendingNotifications: Map<string, NotificationResult> = new Map();

  constructor() {
    this.preferences = this.loadPreferences();
    this.initializeAudio();
  }

  // =============================================================================
  // PREFERENCE MANAGEMENT
  // =============================================================================

  getPreferences(): NotificationPreferences {
    return { ...this.preferences };
  }

  updatePreferences(updates: Partial<NotificationPreferences>): void {
    this.preferences = { ...this.preferences, ...updates };
    this.savePreferences();
  }

  private loadPreferences(): NotificationPreferences {
    try {
      const stored = localStorage.getItem('notification-preferences');
      return stored ? { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) } : DEFAULT_PREFERENCES;
    } catch (error) {
      console.warn('Failed to load notification preferences:', error);
      return DEFAULT_PREFERENCES;
    }
  }

  private savePreferences(): void {
    try {
      localStorage.setItem('notification-preferences', JSON.stringify(this.preferences));
    } catch (error) {
      console.warn('Failed to save notification preferences:', error);
    }
  }

  // =============================================================================
  // AUDIO SYSTEM
  // =============================================================================

  private initializeAudio(): void {
    if (typeof window !== 'undefined' && window.AudioContext) {
      try {
        this.audioContext = new AudioContext();
        this.preloadSounds();
      } catch (error) {
        console.warn('Audio context initialization failed:', error);
      }
    }
  }

  private async preloadSounds(): Promise<void> {
    if (!this.audioContext) return;

    const loadSound = async (name: string, url: string) => {
      try {
        const response = await fetch(url);
        const arrayBuffer = await response.arrayBuffer();
        const audioBuffer = await this.audioContext!.decodeAudioData(arrayBuffer);
        this.audioCache.set(name, audioBuffer);
      } catch (error) {
        console.warn(`Failed to preload sound ${name}:`, error);
      }
    };

    // Preload alert tones
    await Promise.all(
      Object.entries(ALERT_TONES).map(([name, url]) => loadSound(name, url))
    );
  }

  private async playSound(tone: string = 'default'): Promise<void> {
    if (!this.preferences.sound.enabled || !this.audioContext) return;

    try {
      // Resume audio context if suspended (required by some browsers)
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      const buffer = this.audioCache.get(tone);
      if (!buffer) {
        console.warn(`Sound ${tone} not found in cache`);
        return;
      }

      const source = this.audioContext.createBufferSource();
      const gainNode = this.audioContext.createGain();
      
      source.buffer = buffer;
      gainNode.gain.value = this.preferences.sound.volume;
      
      source.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
      
      source.start();
    } catch (error) {
      console.warn('Failed to play notification sound:', error);
    }
  }

  // =============================================================================
  // NOTIFICATION DELIVERY
  // =============================================================================

  async deliverAlert(alert: AlertFiredMessage): Promise<NotificationResult> {
    const notificationId = `alert-${alert.data.alert_id}-${Date.now()}`;
    const result: NotificationResult = {
      id: notificationId,
      alertId: alert.data.alert_id,
      deliveryStatus: [],
      totalChannels: 0,
      successfulChannels: 0
    };

    this.pendingNotifications.set(notificationId, result);

    // Deliver to enabled channels in parallel
    const deliveryPromises: Promise<void>[] = [];

    if (this.preferences.inApp.enabled) {
      result.totalChannels++;
      deliveryPromises.push(this.deliverInApp(alert, result));
    }

    if (this.preferences.sound.enabled) {
      result.totalChannels++;
      deliveryPromises.push(this.deliverSound(alert, result));
    }

    if (this.preferences.slack.enabled && this.preferences.slack.webhookUrl) {
      result.totalChannels++;
      deliveryPromises.push(this.deliverSlack(alert, result));
    }

    // Execute all deliveries in parallel
    await Promise.allSettled(deliveryPromises);

    this.pendingNotifications.delete(notificationId);
    return result;
  }

  private async deliverInApp(alert: AlertFiredMessage, result: NotificationResult): Promise<void> {
    const startTime = Date.now();
    
    try {
      const message = this.formatAlertMessage(alert);
      const toastOptions: ToastOptions = {
        position: this.preferences.inApp.position,
        autoClose: this.preferences.inApp.autoClose,
        hideProgressBar: false,
        closeOnClick: true,
        pauseOnHover: true,
        draggable: true,
        className: 'alert-toast',
        bodyClassName: 'alert-toast-body',
        progressClassName: 'alert-toast-progress'
      };

      // Determine toast type based on alert severity/condition
      const alertType = this.getAlertType(alert);
      let toastId: ToastId;

      switch (alertType) {
        case 'warning':
          toastId = toast.warn(message, toastOptions);
          break;
        case 'error':
          toastId = toast.error(message, toastOptions);
          break;
        case 'success':
          toastId = toast.success(message, toastOptions);
          break;
        default:
          toastId = toast.info(message, toastOptions);
      }

      result.deliveryStatus.push({
        channel: 'in-app',
        status: 'delivered',
        timestamp: new Date().toISOString()
      });
      result.successfulChannels++;

      // Play sound if enabled
      if (this.preferences.inApp.sound && this.preferences.sound.enabled) {
        this.playSound(this.preferences.sound.alertTone);
      }

    } catch (error) {
      result.deliveryStatus.push({
        channel: 'in-app',
        status: 'failed',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  private async deliverSound(alert: AlertFiredMessage, result: NotificationResult): Promise<void> {
    try {
      await this.playSound(this.preferences.sound.alertTone);
      
      result.deliveryStatus.push({
        channel: 'sound',
        status: 'delivered',
        timestamp: new Date().toISOString()
      });
      result.successfulChannels++;
    } catch (error) {
      result.deliveryStatus.push({
        channel: 'sound',
        status: 'failed',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Sound playback failed'
      });
    }
  }

  private async deliverSlack(alert: AlertFiredMessage, result: NotificationResult): Promise<void> {
    if (!this.preferences.slack.webhookUrl) {
      result.deliveryStatus.push({
        channel: 'slack',
        status: 'failed',
        timestamp: new Date().toISOString(),
        error: 'Webhook URL not configured'
      });
      return;
    }

    try {
      const slackMessage = this.formatSlackMessage(alert);
      
      const response = await fetch(this.preferences.slack.webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(slackMessage)
      });

      if (!response.ok) {
        throw new Error(`Slack API error: ${response.status} ${response.statusText}`);
      }

      result.deliveryStatus.push({
        channel: 'slack',
        status: 'delivered',
        timestamp: new Date().toISOString()
      });
      result.successfulChannels++;
    } catch (error) {
      result.deliveryStatus.push({
        channel: 'slack',
        status: 'failed',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Slack delivery failed'
      });
    }
  }

  // =============================================================================
  // MESSAGE FORMATTING
  // =============================================================================

  private formatAlertMessage(alert: AlertFiredMessage): React.ReactNode {
    const { data } = alert;
    const condition = data.rule_condition.replace('_', ' ').toLowerCase();
    
    return (
      <div className="alert-notification">
        <div className="alert-title">
          <strong>{data.symbol}</strong> Alert Triggered
        </div>
        <div className="alert-details">
          Price {condition} {data.threshold_value.toFixed(4)} (Current: {data.trigger_value.toFixed(4)})
        </div>
        <div className="alert-timestamp">
          {new Date(alert.timestamp).toLocaleTimeString()}
        </div>
      </div>
    );
  }

  private formatSlackMessage(alert: AlertFiredMessage) {
    const { data } = alert;
    const condition = data.rule_condition.replace('_', ' ');
    
    return {
      username: this.preferences.slack.username || 'TradeAssist',
      channel: this.preferences.slack.channel,
      icon_emoji: ':chart_with_upwards_trend:',
      attachments: [
        {
          color: this.getSlackColor(alert),
          title: `${data.symbol} Alert Triggered`,
          text: data.message,
          fields: [
            {
              title: 'Symbol',
              value: data.symbol,
              short: true
            },
            {
              title: 'Condition',
              value: condition,
              short: true
            },
            {
              title: 'Threshold',
              value: data.threshold_value.toFixed(4),
              short: true
            },
            {
              title: 'Current Value',
              value: data.trigger_value.toFixed(4),
              short: true
            }
          ],
          footer: 'TradeAssist',
          ts: Math.floor(new Date(alert.timestamp).getTime() / 1000)
        }
      ]
    };
  }

  private getAlertType(alert: AlertFiredMessage): 'info' | 'success' | 'warning' | 'error' {
    const condition = alert.data.rule_condition.toLowerCase();
    
    if (condition.includes('above') || condition.includes('up')) {
      return 'success';
    } else if (condition.includes('below') || condition.includes('down')) {
      return 'warning';
    } else if (condition.includes('error')) {
      return 'error';
    } else {
      return 'info';
    }
  }

  private getSlackColor(alert: AlertFiredMessage): string {
    const alertType = this.getAlertType(alert);
    
    switch (alertType) {
      case 'success': return 'good';
      case 'warning': return 'warning';
      case 'error': return 'danger';
      default: return '#36a64f';
    }
  }

  // =============================================================================
  // UTILITY METHODS
  // =============================================================================

  testNotification(channel: keyof NotificationPreferences): void {
    const testAlert: AlertFiredMessage = {
      type: 'alert_fired',
      timestamp: new Date().toISOString(),
      data: {
        alert_id: 999,
        rule_id: 1,
        instrument_id: 1,
        symbol: 'TEST',
        trigger_value: 4250.50,
        threshold_value: 4250.00,
        rule_condition: 'above',
        message: 'This is a test notification to verify your settings are working correctly.'
      }
    };

    switch (channel) {
      case 'inApp':
        this.deliverInApp(testAlert, {
          id: 'test',
          alertId: 999,
          deliveryStatus: [],
          totalChannels: 1,
          successfulChannels: 0
        });
        break;
      case 'sound':
        this.playSound(this.preferences.sound.alertTone);
        break;
      case 'slack':
        this.deliverSlack(testAlert, {
          id: 'test',
          alertId: 999,
          deliveryStatus: [],
          totalChannels: 1,
          successfulChannels: 0
        });
        break;
    }
  }

  getAvailableSounds(): Array<{ value: string; label: string }> {
    return Object.keys(ALERT_TONES).map(tone => ({
      value: tone,
      label: tone.charAt(0).toUpperCase() + tone.slice(1)
    }));
  }

  clearAllNotifications(): void {
    toast.dismiss();
  }

  // Cleanup method
  destroy(): void {
    this.clearAllNotifications();
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }
    this.audioCache.clear();
    this.pendingNotifications.clear();
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

export const notificationService = new NotificationService();