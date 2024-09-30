# services/audit_service/audit/models.py

from mongoengine import Document, fields

class AuditLog(Document):
    user_id = fields.IntField(required=True)
    action = fields.StringField(required=True)
    resource = fields.StringField(required=True)
    timestamp = fields.DateTimeField(required=True)
    ip_address = fields.StringField()
    user_agent = fields.StringField()
    status_code = fields.IntField()
    request_data = fields.DictField()
    response_data = fields.DictField()
    error_message = fields.StringField()
