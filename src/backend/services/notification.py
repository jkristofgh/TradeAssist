"""
Notification Service.

Multi-channel notification delivery for trading alerts including
sound alerts, Slack notifications, and in-app notifications.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum

import structlog
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from ..config import settings
from .secret_manager import secret_manager
from .circuit_breaker import circuit_breaker, CircuitBreakerConfig

logger = structlog.get_logger()


class NotificationChannel(str, Enum):
    """Available notification channels."""
    IN_APP = "in_app"
    SOUND = "sound"
    SLACK = "slack"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SoundManager:
    """
    Sound notification manager using pygame.
    
    Handles sound alert playback with different sound types
    for various alert priorities and conditions.
    """
    
    def __init__(self):
        self.enabled = settings.SOUND_ALERTS_ENABLED
        self._initialized = False
        self._sound_cache: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """Initialize pygame mixer for sound playback."""
        if not self.enabled or self._initialized:
            return
        
        try:
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self._initialized = True
            logger.info("Sound manager initialized")
        except ImportError:
            logger.warning("pygame not available, sound alerts disabled")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize sound manager: {e}")
            self.enabled = False
    
    async def play_alert_sound(self, priority: NotificationPriority = NotificationPriority.NORMAL) -> bool:
        """
        Play alert sound based on priority.
        
        Args:
            priority: Alert priority level.
        
        Returns:
            bool: True if sound played successfully.
        """
        if not self.enabled or not self._initialized:
            return False
        
        try:
            import pygame
            
            # Generate tone based on priority (since we don't have audio files)
            duration = 0.5  # 500ms
            sample_rate = 22050
            
            if priority == NotificationPriority.URGENT:
                frequency = 1000  # High pitch for urgent
                duration = 1.0
            elif priority == NotificationPriority.HIGH:
                frequency = 800   # Medium-high pitch
                duration = 0.7
            else:
                frequency = 600   # Standard pitch
            
            # Generate simple sine wave tone
            import numpy as np
            frames = int(duration * sample_rate)
            arr = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
            arr = (arr * 32767).astype(np.int16)
            
            # Convert to stereo
            stereo_arr = np.zeros((frames, 2), dtype=np.int16)
            stereo_arr[:, 0] = arr
            stereo_arr[:, 1] = arr
            
            # Play sound
            sound = pygame.sndarray.make_sound(stereo_arr)
            sound.play()
            
            logger.debug(f"Played {priority} priority alert sound")
            return True
            
        except ImportError:
            logger.warning("numpy not available for sound generation")
            return False
        except Exception as e:
            logger.error(f"Failed to play alert sound: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup sound resources."""
        if self._initialized:
            try:
                import pygame
                pygame.mixer.quit()
                logger.debug("Sound manager cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up sound manager: {e}")


class SlackNotifier:
    """
    Slack notification manager.
    
    Sends trading alert notifications to Slack channels with
    formatting and error handling.
    """
    
    def __init__(self):
        self.enabled = bool(settings.SLACK_BOT_TOKEN)
        self.client: Optional[AsyncWebClient] = None
        self.default_channel = settings.SLACK_CHANNEL
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize Slack client with secure token from Secret Manager."""
        if self._initialized:
            return
        
        try:
            # Try to get token from Secret Manager first
            slack_token = await secret_manager.get_secret(
                "slack-bot-token",
                fallback_env_var="SLACK_BOT_TOKEN"
            )
            
            if slack_token:
                self.client = AsyncWebClient(token=slack_token)
                self.enabled = True
                logger.info("Slack notifier initialized with secure token")
            else:
                self.enabled = False
                logger.warning("Slack token not found, notifications disabled")
                
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Slack client: {e}")
            self.enabled = False
            self._initialized = True
    
    @circuit_breaker("slack_notifications", config=CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60,
        request_timeout=15.0
    ))
    async def _send_slack_message(self, target_channel: str, formatted_message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to Slack with circuit breaker protection."""
        return await self.client.chat_postMessage(
            channel=target_channel,
            **formatted_message
        )
    
    async def send_alert(
        self,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channel: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send alert notification to Slack.
        
        Args:
            message: Alert message text.
            priority: Alert priority level.
            channel: Slack channel (uses default if not specified).
            additional_data: Additional context data.
        
        Returns:
            bool: True if message sent successfully.
        """
        # Ensure initialization
        await self.initialize()
        
        if not self.enabled or not self.client:
            return False
        
        target_channel = channel or self.default_channel
        
        try:
            # Format message based on priority
            formatted_message = self._format_slack_message(message, priority, additional_data)
            
            # Send to Slack with circuit breaker
            response = await self._send_slack_message(target_channel, formatted_message)
            
            if response["ok"]:
                logger.debug(f"Slack alert sent to {target_channel}")
                return True
            else:
                logger.error(f"Slack API error: {response.get('error', 'Unknown error')}")
                return False
                
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False
    
    def _format_slack_message(
        self,
        message: str,
        priority: NotificationPriority,
        additional_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Format message for Slack with priority-based styling.
        
        Args:
            message: Base alert message.
            priority: Alert priority.
            additional_data: Additional context.
        
        Returns:
            Dict: Slack message payload.
        """
        # Priority-based emoji and color
        priority_config = {
            NotificationPriority.LOW: {"emoji": "📊", "color": "#36a64f"},
            NotificationPriority.NORMAL: {"emoji": "⚠️", "color": "#ff9900"},
            NotificationPriority.HIGH: {"emoji": "🚨", "color": "#ff0000"},
            NotificationPriority.URGENT: {"emoji": "🔥", "color": "#8b0000"},
        }
        
        config = priority_config.get(priority, priority_config[NotificationPriority.NORMAL])
        
        # Build message
        formatted_text = f"{config['emoji']} {message}"
        
        payload = {
            "text": formatted_text,
            "attachments": []
        }
        
        # Add context attachment for high priority alerts
        if priority in [NotificationPriority.HIGH, NotificationPriority.URGENT] and additional_data:
            attachment = {
                "color": config["color"],
                "fields": [],
                "ts": int(datetime.now(timezone.utc).timestamp())
            }
            
            # Add relevant fields
            for key, value in additional_data.items():
                if key in ["evaluation_time_ms", "threshold", "percent_change"]:
                    attachment["fields"].append({
                        "title": key.replace("_", " ").title(),
                        "value": str(value),
                        "short": True
                    })
            
            if attachment["fields"]:
                payload["attachments"].append(attachment)
        
        return payload


class NotificationService:
    """
    Multi-channel notification delivery service.
    
    Coordinates notification delivery across multiple channels (sound, Slack, in-app)
    with priority handling, delivery tracking, and error management.
    """
    
    def __init__(self):
        self.sound_manager = SoundManager()
        self.slack_notifier = SlackNotifier()
        
        # Delivery tracking
        self.notifications_sent = 0
        self.delivery_failures = 0
        
    async def initialize(self) -> None:
        """Initialize notification service and all channels."""
        await self.sound_manager.initialize()
        await self.slack_notifier.initialize()
        logger.info("Notification service initialized")
    
    async def send_alert_notification(
        self,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: List[NotificationChannel] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[NotificationChannel, bool]:
        """
        Send alert notification through specified channels.
        
        Args:
            message: Alert message text.
            priority: Alert priority level.
            channels: List of channels to notify (all by default).
            additional_data: Additional context data.
        
        Returns:
            Dict: Delivery status for each channel.
        """
        if channels is None:
            channels = [NotificationChannel.IN_APP, NotificationChannel.SOUND, NotificationChannel.SLACK]
        
        delivery_results = {}
        
        # Send through each channel
        for channel in channels:
            try:
                if channel == NotificationChannel.SOUND:
                    success = await self.sound_manager.play_alert_sound(priority)
                    
                elif channel == NotificationChannel.SLACK:
                    success = await self.slack_notifier.send_alert(
                        message, priority, additional_data=additional_data
                    )
                    
                elif channel == NotificationChannel.IN_APP:
                    # In-app notifications are handled via WebSocket broadcasting
                    success = True  # Always successful for in-app
                    
                else:
                    success = False
                
                delivery_results[channel] = success
                
                if success:
                    self.notifications_sent += 1
                else:
                    self.delivery_failures += 1
                    
            except Exception as e:
                logger.error(f"Error sending notification via {channel}: {e}")
                delivery_results[channel] = False
                self.delivery_failures += 1
        
        return delivery_results
    
    async def cleanup(self) -> None:
        """Cleanup notification service resources."""
        await self.sound_manager.cleanup()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get notification service statistics.
        
        Returns:
            Dict: Notification delivery statistics.
        """
        return {
            "notifications_sent": self.notifications_sent,
            "delivery_failures": self.delivery_failures,
            "sound_enabled": self.sound_manager.enabled,
            "slack_enabled": self.slack_notifier.enabled,
        }