# notification/models.py
from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime
import pytz
from typing import List, Dict

class NotificationChannel(EmbeddedDocument):
    """Channel configuration for notifications"""
    type = fields.StringField(required=True, choices=[
        'EMAIL', 'SMS', 'PUSH', 'IN_APP'
    ])
    config = fields.DictField()
    is_enabled = fields.BooleanField(default=True)
    last_used = fields.DateTimeField()
    failure_count = fields.IntField(default=0)

class NotificationTemplate(Document):
    name = fields.StringField(required=True, unique=True)
    type = fields.StringField(required=True, choices=[
        'EMAIL', 'SMS', 'PUSH', 'IN_APP'
    ])
    subject = fields.StringField()
    content = fields.StringField(required=True)
    html_content = fields.StringField()  # For email templates
    variables = fields.ListField(fields.StringField())
    category = fields.StringField()
    is_active = fields.BooleanField(default=True)
    version = fields.IntField(default=1)
    created_by = fields.StringField()
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'notification_templates',
        'indexes': [
            'name',
            'type',
            'is_active',
            ('name', 'version')
        ]
    }

    def clean(self):
        self.updated_at = datetime.utcnow()

class NotificationPreference(EmbeddedDocument):
    channel = fields.StringField(required=True, choices=[
        'EMAIL', 'SMS', 'PUSH', 'IN_APP'
    ])
    enabled = fields.BooleanField(default=True)
    quiet_hours_start = fields.IntField(min_value=0, max_value=23)
    quiet_hours_end = fields.IntField(min_value=0, max_value=23)
    frequency = fields.StringField(choices=[
        'IMMEDIATE', 'DAILY_DIGEST', 'WEEKLY_DIGEST'
    ], default='IMMEDIATE')

class UserDevice(EmbeddedDocument):
    device_id = fields.StringField(required=True)
    device_type = fields.StringField(choices=['IOS', 'ANDROID', 'WEB'])
    push_token = fields.StringField()
    is_active = fields.BooleanField(default=True)
    last_used = fields.DateTimeField()

class UserNotificationSettings(Document):
    user_id = fields.UUIDField(required=True, unique=True)
    email = fields.StringField()
    phone_number = fields.StringField()
    preferences = fields.EmbeddedDocumentListField(NotificationPreference)
    categories_muted = fields.ListField(fields.StringField())
    devices = fields.EmbeddedDocumentListField(UserDevice)
    is_active = fields.BooleanField(default=True)
    language = fields.StringField(default='en')
    timezone = fields.StringField(default='UTC')
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'user_notification_settings',
        'indexes': [
            'user_id',
            'email',
            'phone_number'
        ]
    }

    def clean(self):
        self.updated_at = datetime.utcnow()

    def get_active_channels(self) -> List[str]:
        """Get list of active notification channels for user"""
        return [pref.channel for pref in self.preferences if pref.enabled]

    def is_in_quiet_hours(self, channel: str) -> bool:
        """Check if current time is within quiet hours for channel"""
        pref = next((p for p in self.preferences if p.channel == channel), None)
        if not pref or not pref.quiet_hours_start or not pref.quiet_hours_end:
            return False

        tz = pytz.timezone(self.timezone)
        current_hour = datetime.now(tz).hour
        if pref.quiet_hours_start <= pref.quiet_hours_end:
            return pref.quiet_hours_start <= current_hour <= pref.quiet_hours_end
        return current_hour >= pref.quiet_hours_start or current_hour <= pref.quiet_hours_end

class Notification(Document):
    user_id = fields.UUIDField(required=True)
    type = fields.StringField(required=True, choices=[
        'TRANSACTION', 'SECURITY', 'ACCOUNT', 'MARKETING',
        'SYSTEM', 'FRAUD_ALERT', 'PAYMENT', 'LOAN'
    ])
    priority = fields.StringField(required=True, choices=[
        'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    ])
    title = fields.StringField(required=True)
    content = fields.StringField(required=True)
    template_name = fields.StringField()
    
    # Delivery configuration and status
    channels = fields.ListField(fields.StringField())
    status = fields.DictField()  # Status per channel
    delivery_attempts = fields.IntField(default=0)
    max_attempts = fields.IntField(default=3)
    
    # Read status
    read = fields.BooleanField(default=False)
    read_at = fields.DateTimeField()
    
    # Additional data
    metadata = fields.DictField()
    category = fields.StringField()
    action_url = fields.StringField()
    deep_link = fields.StringField()
    
    # Reference data
    reference_id = fields.StringField()  # Related transaction/event ID
    reference_type = fields.StringField()  # Type of reference (transaction, security event, etc)
    
    # Timing
    created_at = fields.DateTimeField(default=datetime.utcnow)
    scheduled_at = fields.DateTimeField()
    sent_at = fields.DateTimeField()
    expires_at = fields.DateTimeField()
    last_attempt = fields.DateTimeField()

    meta = {
        'collection': 'notifications',
        'indexes': [
            'user_id',
            'type',
            'read',
            'created_at',
            ('user_id', 'read'),
            ('user_id', 'type'),
            ('user_id', '-created_at'),
            'reference_id',
            'scheduled_at'
        ]
    }

    def mark_as_read(self):
        """Mark notification as read"""
        self.read = True
        self.read_at = datetime.utcnow()
        self.save()

    def update_status(self, channel: str, status: str, error: str = None):
        """Update delivery status for specific channel"""
        if not self.status:
            self.status = {}
        self.status[channel] = {
            'status': status,
            'updated_at': datetime.utcnow(),
            'error': error
        }
        if status == 'SENT':
            self.sent_at = datetime.utcnow()
        self.save()

class NotificationBatch(Document):
    template_name = fields.StringField(required=True)
    type = fields.StringField(required=True)
    title = fields.StringField(required=True)
    content = fields.StringField(required=True)
    user_filter = fields.DictField()
    
    priority = fields.StringField(choices=[
        'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    ], default='LOW')
    
    status = fields.StringField(choices=[
        'DRAFT', 'SCHEDULED', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED'
    ], default='DRAFT')
    
    channels = fields.ListField(fields.StringField())
    metadata = fields.DictField()
    category = fields.StringField()
    action_url = fields.StringField()
    
    scheduled_at = fields.DateTimeField()
    expires_at = fields.DateTimeField()
    processed_count = fields.IntField(default=0)
    failed_count = fields.IntField(default=0)
    total_recipients = fields.IntField()
    
    created_by = fields.UUIDField()
    created_at = fields.DateTimeField(default=datetime.utcnow)
    started_at = fields.DateTimeField()
    completed_at = fields.DateTimeField()

    meta = {
        'collection': 'notification_batches',
        'indexes': [
            'status',
            'scheduled_at',
            'created_at',
            'created_by'
        ]
    }

    def update_progress(self, processed: int = 0, failed: int = 0):
        """Update batch processing progress"""
        self.processed_count += processed
        self.failed_count += failed
        if self.processed_count + self.failed_count >= self.total_recipients:
            self.status = 'COMPLETED'
            self.completed_at = datetime.utcnow()
        self.save()