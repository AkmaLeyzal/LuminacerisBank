# services/notification_service/notification/models.py

from mongoengine import Document, IntField, StringField, BooleanField, DateTimeField, DictField
from datetime import datetime

class Notification(Document):
    user_id = IntField(required=True)
    title = StringField(required=True, max_length=255)
    message = StringField(required=True)
    notification_type = StringField(required=True, choices=[
        ('Transaksi', 'Transaksi'),
        ('Pembayaran', 'Pembayaran'),
        ('Peringatan', 'Peringatan')
    ])
    is_read = BooleanField(default=False)
    timestamp = DateTimeField(default=datetime.utcnow)
    metadata = DictField()

    meta = {
    'collection': 'notifications',
    'indexes': ['user_id', 'is_read', 'notification_type', 'timestamp']
    }


    def __str__(self):
        return f"{self.title} to User {self.user_id}"
