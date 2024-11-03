# notification_service/notification/models.py
from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime

class NotificationTemplate(Document):
    name = fields.StringField(required=True, unique=True)
    type = fields.StringField(required=True, choices=[
        'EMAIL', 'SMS', 'PUSH', 'IN_APP'
    ])
    subject = fields.StringField()
    content = fields.StringField(required=True)
    variables = fields.ListField(fields.StringField())
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'notification_templates',
        'indexes': [
            'name',
            'type',
            'is_active'
        ]
    }

class NotificationPreference(EmbeddedDocument):
    channel = fields.StringField(required=True)
    enabled = fields.BooleanField(default=True)
    quiet_hours_start = fields.IntField(min_value=0, max_value=23)
    quiet_hours_end = fields.IntField(min_value=0, max_value=23)

class UserNotificationSettings(Document):
    user_id = fields.IntField(required=True, unique=True)
    preferences = fields.EmbeddedDocumentListField(NotificationPreference)
    categories_muted = fields.ListField(fields.StringField())
    devices = fields.ListField(fields.DictField())
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'user_notification_settings',
        'indexes': [
            'user_id'
        ]
    }

class Notification(Document):
    user_id = fields.IntField(required=True)
    type = fields.StringField(required=True, choices=[
        'TRANSACTION', 'SECURITY', 'ACCOUNT', 'MARKETING',
        'SYSTEM', 'FRAUD_ALERT', 'PAYMENT', 'LOAN'
    ])
    priority = fields.StringField(choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
    title = fields.StringField(required=True)
    content = fields.StringField(required=True)
    template_name = fields.StringField()
    
    # Delivery status
    channels = fields.ListField(fields.StringField())
    status = fields.DictField()  # Status per channel
    read = fields.BooleanField(default=False)
    read_at = fields.DateTimeField()
    
    # Additional data
    metadata = fields.DictField()
    category = fields.StringField()
    action_url = fields.StringField()
    
    # Tracking
    created_at = fields.DateTimeField(default=datetime.utcnow)
    scheduled_at = fields.DateTimeField()
    sent_at = fields.DateTimeField()
    expires_at = fields.DateTimeField()

    meta = {
        'collection': 'notifications',
        'indexes': [
            'user_id',
            'type',
            'read',
            'created_at',
            ('user_id', 'read'),
            ('user_id', 'type'),
            ('user_id', '-created_at')
        ]
    }

class NotificationBatch(Document):
    template_name = fields.StringField(required=True)
    type = fields.StringField(required=True)
    title = fields.StringField(required=True)
    content = fields.StringField(required=True)
    user_filter = fields.DictField()  # Criteria for user selection
    status = fields.StringField(choices=[
        'DRAFT', 'SCHEDULED', 'PROCESSING', 'COMPLETED', 'FAILED'
    ])
    scheduled_at = fields.DateTimeField()
    processed_count = fields.IntField(default=0)
    failed_count = fields.IntField(default=0)
    created_by = fields.IntField()  # Admin user ID
    created_at = fields.DateTimeField(default=datetime.utcnow)
    completed_at = fields.DateTimeField()

    meta = {
        'collection': 'notification_batches',
        'indexes': [
            'status',
            'scheduled_at',
            'created_at'
        ]
    }