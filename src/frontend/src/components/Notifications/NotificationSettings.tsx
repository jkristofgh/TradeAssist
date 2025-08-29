/**
 * NotificationSettings Component
 * 
 * Complete notification preferences configuration interface with real-time testing,
 * channel management, and delivery status monitoring.
 */

import React, { useState, useCallback } from 'react';
import { useNotificationPreferences, useNotificationHistory } from '../../context/NotificationContext';
import { notificationService } from '../../services/notificationService';
import { ToastPosition } from 'react-toastify';

// =============================================================================
// TYPES
// =============================================================================

interface NotificationSettingsProps {
  className?: string;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const TOAST_POSITIONS: Array<{ value: ToastPosition; label: string }> = [
  { value: 'top-left', label: 'Top Left' },
  { value: 'top-right', label: 'Top Right' },
  { value: 'top-center', label: 'Top Center' },
  { value: 'bottom-left', label: 'Bottom Left' },
  { value: 'bottom-right', label: 'Bottom Right' },
  { value: 'bottom-center', label: 'Bottom Center' }
];

const AUTO_CLOSE_OPTIONS = [
  { value: 3000, label: '3 seconds' },
  { value: 5000, label: '5 seconds' },
  { value: 10000, label: '10 seconds' },
  { value: 15000, label: '15 seconds' },
  { value: false, label: 'Manual close only' }
];

// =============================================================================
// MAIN COMPONENT
// =============================================================================

const NotificationSettings: React.FC<NotificationSettingsProps> = ({ className = '' }) => {
  const {
    preferences,
    updateInAppPreferences,
    updateSoundPreferences,
    updateSlackPreferences,
    updateEmailPreferences,
    testNotification
  } = useNotificationPreferences();
  
  const { deliveryHistory, isConnected, getDeliveryStats } = useNotificationHistory();
  
  const [slackConfig, setSlackConfig] = useState({
    webhookUrl: preferences.slack.webhookUrl || '',
    channel: preferences.slack.channel || '',
    username: preferences.slack.username || 'TradeAssist'
  });
  
  const [emailAddresses, setEmailAddresses] = useState(
    preferences.email.addresses.join(', ')
  );
  
  const [testingChannel, setTestingChannel] = useState<string | null>(null);
  
  // Get delivery statistics
  const deliveryStats = getDeliveryStats();
  const availableSounds = notificationService.getAvailableSounds();

  // =============================================================================
  // EVENT HANDLERS
  // =============================================================================

  const handleSlackConfigSave = useCallback(() => {
    updateSlackPreferences({
      webhookUrl: slackConfig.webhookUrl.trim() || undefined,
      channel: slackConfig.channel.trim() || undefined,
      username: slackConfig.username.trim() || undefined
    });
  }, [slackConfig, updateSlackPreferences]);

  const handleEmailAddressesSave = useCallback(() => {
    const addresses = emailAddresses
      .split(',')
      .map(email => email.trim())
      .filter(email => email && email.includes('@'));
    
    updateEmailPreferences({ addresses });
  }, [emailAddresses, updateEmailPreferences]);

  const handleTestNotification = useCallback(async (channel: keyof typeof preferences) => {
    setTestingChannel(channel);
    try {
      testNotification(channel);
      // Reset testing state after delay
      setTimeout(() => setTestingChannel(null), 2000);
    } catch (error) {
      console.error('Test notification failed:', error);
      setTestingChannel(null);
    }
  }, [testNotification]);

  return (
    <div className={`notification-settings ${className}`}>
      <div className=\"settings-header\">
        <h2>Notification Settings</h2>
        <div className=\"connection-status\">
          <div 
            className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}
          ></div>
          <span>WebSocket {isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      {/* Delivery Statistics */}
      {deliveryHistory.length > 0 && (
        <div className=\"delivery-stats\">
          <h3>Delivery Statistics</h3>
          <div className=\"stats-grid\">
            <div className=\"stat-card\">
              <div className=\"stat-value\">{deliveryStats.total}</div>
              <div className=\"stat-label\">Total Alerts</div>
            </div>
            <div className=\"stat-card\">
              <div className=\"stat-value\">{deliveryStats.successRate.toFixed(1)}%</div>
              <div className=\"stat-label\">Success Rate</div>
            </div>
            <div className=\"stat-card\">
              <div className=\"stat-value\">{deliveryStats.successful}</div>
              <div className=\"stat-label\">Successful Deliveries</div>
            </div>
          </div>
        </div>
      )}

      {/* In-App Notifications */}
      <div className=\"settings-section\">
        <div className=\"section-header\">
          <h3>In-App Notifications</h3>
          <div className=\"section-actions\">
            <label className=\"toggle-switch\">
              <input
                type=\"checkbox\"
                checked={preferences.inApp.enabled}
                onChange={(e) => updateInAppPreferences({ enabled: e.target.checked })}
              />
              <span className=\"toggle-slider\"></span>
            </label>
            <button
              onClick={() => handleTestNotification('inApp')}
              disabled={!preferences.inApp.enabled || testingChannel === 'inApp'}
              className=\"btn btn-sm btn-secondary\"
            >
              {testingChannel === 'inApp' ? 'Testing...' : 'Test'}
            </button>
          </div>
        </div>
        
        {preferences.inApp.enabled && (
          <div className=\"section-content\">
            <div className=\"form-row\">
              <div className=\"form-group\">
                <label>Position:</label>
                <select
                  value={preferences.inApp.position}
                  onChange={(e) => updateInAppPreferences({ position: e.target.value as ToastPosition })}
                  className=\"form-select\"
                >
                  {TOAST_POSITIONS.map(pos => (
                    <option key={pos.value} value={pos.value}>{pos.label}</option>
                  ))}
                </select>
              </div>
              
              <div className=\"form-group\">
                <label>Auto Close:</label>
                <select
                  value={preferences.inApp.autoClose === false ? 'false' : preferences.inApp.autoClose}
                  onChange={(e) => {
                    const value = e.target.value === 'false' ? false : parseInt(e.target.value);
                    updateInAppPreferences({ autoClose: value });
                  }}
                  className=\"form-select\"
                >
                  {AUTO_CLOSE_OPTIONS.map(option => (
                    <option key={String(option.value)} value={String(option.value)}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className=\"form-group\">
              <label className=\"checkbox-label\">
                <input
                  type=\"checkbox\"
                  checked={preferences.inApp.sound}
                  onChange={(e) => updateInAppPreferences({ sound: e.target.checked })}
                />
                Play sound with in-app notifications
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Sound Notifications */}
      <div className=\"settings-section\">
        <div className=\"section-header\">
          <h3>Sound Notifications</h3>
          <div className=\"section-actions\">
            <label className=\"toggle-switch\">
              <input
                type=\"checkbox\"
                checked={preferences.sound.enabled}
                onChange={(e) => updateSoundPreferences({ enabled: e.target.checked })}
              />
              <span className=\"toggle-slider\"></span>
            </label>
            <button
              onClick={() => handleTestNotification('sound')}
              disabled={!preferences.sound.enabled || testingChannel === 'sound'}
              className=\"btn btn-sm btn-secondary\"
            >
              {testingChannel === 'sound' ? 'Testing...' : 'Test'}
            </button>
          </div>
        </div>
        
        {preferences.sound.enabled && (
          <div className=\"section-content\">
            <div className=\"form-row\">
              <div className=\"form-group\">
                <label>Alert Tone:</label>
                <select
                  value={preferences.sound.alertTone}
                  onChange={(e) => updateSoundPreferences({ alertTone: e.target.value })}
                  className=\"form-select\"
                >
                  {availableSounds.map(sound => (
                    <option key={sound.value} value={sound.value}>{sound.label}</option>
                  ))}
                </select>
              </div>
              
              <div className=\"form-group\">
                <label>Volume: {Math.round(preferences.sound.volume * 100)}%</label>
                <input
                  type=\"range\"
                  min=\"0\"
                  max=\"1\"
                  step=\"0.1\"
                  value={preferences.sound.volume}
                  onChange={(e) => updateSoundPreferences({ volume: parseFloat(e.target.value) })}
                  className=\"volume-slider\"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Slack Notifications */}
      <div className=\"settings-section\">
        <div className=\"section-header\">
          <h3>Slack Integration</h3>
          <div className=\"section-actions\">
            <label className=\"toggle-switch\">
              <input
                type=\"checkbox\"
                checked={preferences.slack.enabled}
                onChange={(e) => updateSlackPreferences({ enabled: e.target.checked })}
              />
              <span className=\"toggle-slider\"></span>
            </label>
            <button
              onClick={() => handleTestNotification('slack')}
              disabled={!preferences.slack.enabled || !slackConfig.webhookUrl || testingChannel === 'slack'}
              className=\"btn btn-sm btn-secondary\"
            >
              {testingChannel === 'slack' ? 'Testing...' : 'Test'}
            </button>
          </div>
        </div>
        
        {preferences.slack.enabled && (
          <div className=\"section-content\">
            <div className=\"form-group\">
              <label>Webhook URL: *</label>
              <input
                type=\"url\"
                value={slackConfig.webhookUrl}
                onChange={(e) => setSlackConfig(prev => ({ ...prev, webhookUrl: e.target.value }))}
                placeholder=\"https://hooks.slack.com/services/...\"
                className=\"form-input\"
              />
              <small className=\"form-help\">
                Create a webhook in your Slack workspace settings
              </small>
            </div>
            
            <div className=\"form-row\">
              <div className=\"form-group\">
                <label>Channel (optional):</label>
                <input
                  type=\"text\"
                  value={slackConfig.channel}
                  onChange={(e) => setSlackConfig(prev => ({ ...prev, channel: e.target.value }))}
                  placeholder=\"#alerts\"
                  className=\"form-input\"
                />
              </div>
              
              <div className=\"form-group\">
                <label>Username:</label>
                <input
                  type=\"text\"
                  value={slackConfig.username}
                  onChange={(e) => setSlackConfig(prev => ({ ...prev, username: e.target.value }))}
                  placeholder=\"TradeAssist\"
                  className=\"form-input\"
                />
              </div>
            </div>
            
            <button
              onClick={handleSlackConfigSave}
              className=\"btn btn-primary\"
            >
              Save Slack Configuration
            </button>
          </div>
        )}
      </div>

      {/* Email Notifications (Future Feature) */}
      <div className=\"settings-section\">
        <div className=\"section-header\">
          <h3>Email Notifications</h3>
          <div className=\"section-actions\">
            <label className=\"toggle-switch\">
              <input
                type=\"checkbox\"
                checked={preferences.email.enabled}
                onChange={(e) => updateEmailPreferences({ enabled: e.target.checked })}
                disabled={true} // Disabled for now
              />
              <span className=\"toggle-slider\"></span>
            </label>
            <span className=\"feature-badge\">Coming Soon</span>
          </div>
        </div>
        
        {preferences.email.enabled && (
          <div className=\"section-content\">
            <div className=\"form-group\">
              <label>Email Addresses:</label>
              <textarea
                value={emailAddresses}
                onChange={(e) => setEmailAddresses(e.target.value)}
                placeholder=\"email1@domain.com, email2@domain.com\"
                className=\"form-textarea\"
                rows={3}
                disabled={true}
              />
              <small className=\"form-help\">
                Separate multiple email addresses with commas
              </small>
            </div>
            
            <button
              onClick={handleEmailAddressesSave}
              className=\"btn btn-primary\"
              disabled={true}
            >
              Save Email Configuration
            </button>
          </div>
        )}
      </div>

      {/* Channel Performance */}
      {Object.keys(deliveryStats.channelStats).length > 0 && (
        <div className=\"settings-section\">
          <h3>Channel Performance</h3>
          <div className=\"channel-stats\">
            {Object.entries(deliveryStats.channelStats).map(([channel, stats]) => {
              const successRate = (stats.delivered / stats.total) * 100;
              return (
                <div key={channel} className=\"channel-stat-card\">
                  <div className=\"channel-name\">{channel.charAt(0).toUpperCase() + channel.slice(1)}</div>
                  <div className=\"channel-metrics\">
                    <div className=\"metric\">
                      <span className=\"metric-value\">{stats.delivered}</span>
                      <span className=\"metric-label\">Delivered</span>
                    </div>
                    <div className=\"metric\">
                      <span className=\"metric-value\">{stats.failed}</span>
                      <span className=\"metric-label\">Failed</span>
                    </div>
                    <div className=\"metric\">
                      <span className=\"metric-value\">{successRate.toFixed(1)}%</span>
                      <span className=\"metric-label\">Success Rate</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationSettings;