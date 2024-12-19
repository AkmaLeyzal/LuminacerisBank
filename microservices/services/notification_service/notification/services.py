# notification/services.py
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging
from bson import ObjectId
from django.conf import settings
from django.core.cache import cache
from confluent_kafka import Consumer, Producer, KafkaError
from .models import (
    Notification, NotificationTemplate, UserNotificationSettings,
    NotificationBatch
)
from .utils.email_sender import EmailService
from .utils.sms_sender import SMSService
from .utils.push_sender import PushNotificationService

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.push_service = PushNotificationService()
        self.producer = Producer({
            'bootstrap.servers': settings.KAFKA_SETTINGS['BOOTSTRAP_SERVERS'],
            'security.protocol': settings.KAFKA_SETTINGS['SECURITY_PROTOCOL'],
            'sasl.mechanisms': settings.KAFKA_SETTINGS['SASL_MECHANISMS'],
            'sasl.username': settings.KAFKA_SETTINGS['SASL_USERNAME'],
            'sasl.password': settings.KAFKA_SETTINGS['SASL_PASSWORD']
        })

    def create_notification(
        self,
        user_id: str,
        notification_data: Dict[str, Any]
    ) -> Notification:
        """Create a new notification"""
        try:
            # Get user settings
            settings = self._get_user_settings(user_id)
            if not settings:
                raise ValueError(f"User settings not found for user {user_id}")

            # Determine channels based on user preferences
            channels = self._determine_channels(
                settings,
                notification_data.get('type'),
                notification_data.get('priority')
            )

            # Create notification
            notification = Notification(
                user_id=user_id,
                channels=channels,
                **notification_data
            ).save()

            # Process template if specified
            if template_name := notification_data.get('template_name'):
                self._process_template(notification, template_name)

            # Send via appropriate channels
            self._send_notification(notification, settings)

            return notification

        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise

    def _get_user_settings(
        self,
        user_id: str
    ) -> Optional[UserNotificationSettings]:
        """Get user notification settings with caching"""
        cache_key = f'notification_settings:{user_id}'
        settings = cache.get(cache_key)
        
        if not settings:
            settings = UserNotificationSettings.objects(user_id=user_id).first()
            if settings:
                cache.set(cache_key, settings, timeout=300)  # 5 minutes cache
                
        return settings

    def _determine_channels(
        self,
        user_settings: UserNotificationSettings,
        notification_type: str,
        priority: str
    ) -> List[str]:
        """Determine which channels to use based on settings and type"""
        channels = []
        
        for pref in user_settings.preferences:
            if not pref.enabled:
                continue
                
            # Skip if in quiet hours unless high priority
            if priority not in ['HIGH', 'CRITICAL']:
                if user_settings.is_in_quiet_hours(pref.channel):
                    continue

            # Skip if category is muted
            if notification_type in user_settings.categories_muted:
                continue

            channels.append(pref.channel)

        return channels

    def _process_template(
        self,
        notification: Notification,
        template_name: str
    ) -> None:
        """Process notification template"""
        template = NotificationTemplate.objects(
            name=template_name,
            is_active=True
        ).order_by('-version').first()
        
        if not template:
            raise ValueError(f"Template {template_name} not found")

        # Replace variables in content
        content = template.content
        for var in template.variables:
            if var in notification.metadata:
                content = content.replace(
                    f"{{{var}}}",
                    str(notification.metadata[var])
                )

        notification.content = content
        notification.save()

    def _send_notification(
        self,
        notification: Notification,
        user_settings: UserNotificationSettings
    ) -> None:
        """Send notification through specified channels"""
        for channel in notification.channels:
            try:
                if channel == 'EMAIL' and user_settings.email:
                    self._send_email(notification, user_settings)
                elif channel == 'SMS' and user_settings.phone_number:
                    self._send_sms(notification, user_settings)
                elif channel == 'PUSH':
                    self._send_push(notification, user_settings)
                elif channel == 'IN_APP':
                    self._send_in_app(notification)

            except Exception as e:
                logger.error(
                    f"Error sending {channel} notification: {str(e)}"
                )
                notification.update_status(
                    channel,
                    'FAILED',
                    str(e)
                )

    def _send_email(
        self,
        notification: Notification,
        user_settings: UserNotificationSettings
    ) -> None:
        """Send email notification"""
        try:
            self.email_service.send_email(
                to_email=user_settings.email,
                subject=notification.title,
                content=notification.content,
                template_name=notification.template_name,
                metadata=notification.metadata
            )
            notification.update_status('EMAIL', 'SENT')
        except Exception as e:
            raise Exception(f"Email sending failed: {str(e)}")

    def _send_sms(
        self,
        notification: Notification,
        user_settings: UserNotificationSettings
    ) -> None:
        """Send SMS notification"""
        try:
            self.sms_service.send_sms(
                phone_number=user_settings.phone_number,
                message=notification.content
            )
            notification.update_status('SMS', 'SENT')
        except Exception as e:
            raise Exception(f"SMS sending failed: {str(e)}")

    def _send_push(
        self,
        notification: Notification,
        user_settings: UserNotificationSettings
    ) -> None:
        """Send push notification to user devices"""
        for device in user_settings.devices:
            if not device.is_active or not device.push_token:
                continue

            try:
                self.push_service.send_push(
                    device_token=device.push_token,
                    title=notification.title,
                    body=notification.content,
                    data=notification.metadata
                )
                notification.update_status('PUSH', 'SENT')
            except Exception as e:
                raise Exception(f"Push notification failed: {str(e)}")

    def _send_in_app(self, notification: Notification) -> None:
        """Handle in-app notification"""
        try:
            # Publish to Kafka for real-time delivery
            self.producer.produce(
                topic=settings.KAFKA_SETTINGS['TOPICS']['NOTIFICATION_EVENTS'],
                key=str(notification.user_id),
                value=json.dumps({
                    'event_type': 'NEW_NOTIFICATION',
                    'notification_id': str(notification.id),
                    'user_id': str(notification.user_id),
                    'title': notification.title,
                    'content': notification.content,
                    'type': notification.type,
                    'priority': notification.priority,
                    'timestamp': datetime.utcnow().isoformat()
                })
            )
            notification.update_status('IN_APP', 'SENT')
        except Exception as e:
            raise Exception(f"In-app notification failed: {str(e)}")

    def mark_as_read(
        self,
        notification_id: str,
        user_id: str
    ) -> Notification:
        """Mark notification as read"""
        notification = Notification.objects(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if not notification:
            raise ValueError("Notification not found")
            
        notification.mark_as_read()
        return notification

    def get_unread_count(self, user_id: str) -> Dict[str, Any]:
        """Get unread notification counts"""
        pipeline = [
            {'$match': {
                'user_id': user_id,
                'read': False
            }},
            {'$group': {
                '_id': {
                    'type': '$type'
                },
                'count': {'$sum': 1}
            }}
        ]
        
        results = Notification.objects.aggregate(pipeline)
        
        categories = {}
        total = 0
        for result in results:
            category = result['_id']['type']
            count = result['count']
            categories[category] = count
            total += count
            
        return {
            'unread_count': total,
            'categories': categories
        }

    def create_batch(
        self,
        batch_data: Dict[str, Any],
        created_by: str
    ) -> NotificationBatch:
        """Create a notification batch"""
        try:
            batch = NotificationBatch(
                created_by=created_by,
                **batch_data
            ).save()

            # Start processing if not scheduled
            if not batch.scheduled_at:
                self._process_batch(batch)

            return batch

        except Exception as e:
            logger.error(f"Error creating batch: {str(e)}")
            raise

    def _process_batch(self, batch: NotificationBatch) -> None:
        """Process notification batch"""
        try:
            # Update status
            batch.status = 'PROCESSING'
            batch.started_at = datetime.utcnow()
            batch.save()

            # Get users matching filter
            user_settings = UserNotificationSettings.objects(
                __raw__=batch.user_filter
            )
            batch.total_recipients = user_settings.count()

            # Create notifications for each user
            for settings in user_settings:
                try:
                    self.create_notification(
                        user_id=settings.user_id,
                        notification_data={
                            'type': batch.type,
                            'priority': batch.priority,
                            'title': batch.title,
                            'content': batch.content,
                            'channels': batch.channels,
                            'metadata': batch.metadata,
                            'category': batch.category,
                            'action_url': batch.action_url
                        }
                    )
                    batch.update_progress(processed=1)
                except Exception as e:
                    logger.error(
                        f"Error processing batch notification: {str(e)}"
                    )
                    batch.update_progress(failed=1)

        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            batch.status = 'FAILED'
            batch.save()
            raise