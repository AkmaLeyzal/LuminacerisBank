# services/audit_service/audit/models.py

from mongoengine import Document, IntField, StringField, DateTimeField, DictField
from datetime import datetime

class AuditLog(Document):
    user_id = IntField(required=True)
    action = StringField(required=True, max_length=255)
    resource = StringField(required=True, max_length=255)
    timestamp = DateTimeField(default=datetime.utcnow)
    ip_address = StringField(required=True, max_length=45)  # Mendukung IPv6
    user_agent = StringField(required=True, max_length=512)
    status_code = IntField(required=True)
    request_data = DictField()
    response_data = DictField()
    error_message = StringField(max_length=1024, required=False, default=None)

    meta = {
        'collection': 'audit_logs',
        'indexes': ['user_id', 'action', 'resource', 'timestamp']
    }

    def __str__(self):
        return f"AuditLog {self.id} by User {self.user_id}"
