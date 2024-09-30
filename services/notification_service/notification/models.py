# services/notification_service/notification/models.py

from mongoengine import Document, fields

class Notification(Document):
    user_id = fields.IntField(required=True)
    title = fields.StringField(required=True, max_length=255)
    message = fields.StringField(required=True)
    notification_type = fields.StringField(required=True, choices=['Transaction', 'Payment', 'Alert'])
    is_read = fields.BooleanField(default=False)
    timestamp = fields.DateTimeField(required=True)
    metadata = fields.DictField()
