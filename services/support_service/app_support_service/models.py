from django.db import models
# services/support_service/support/models.py

from mongoengine import Document, fields
from datetime import datetime

class Response(fields.EmbeddedDocument):
    responder_id = fields.IntField()
    message = fields.StringField(required=True)
    timestamp = fields.DateTimeField(default=datetime.utcnow)

class SupportTicket(Document):
    ticket_number = fields.StringField(required=True, unique=True)
    user_id = fields.IntField(required=True)
    subject = fields.StringField(required=True)
    description = fields.StringField(required=True)
    category = fields.StringField(required=True, choices=['Technical', 'Account', 'Payment'])
    status = fields.StringField(required=True, choices=['New', 'In Progress', 'Resolved'], default='New')
    priority = fields.StringField(required=True, choices=['Low', 'Medium', 'High'], default='Medium')
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField()
    assigned_to = fields.IntField(null=True)
    responses = fields.EmbeddedDocumentListField(Response)
