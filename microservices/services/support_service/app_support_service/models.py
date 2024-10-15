# services/support_service/support/models.py

from mongoengine import Document, StringField, IntField, DateTimeField, ListField, EmbeddedDocument, EmbeddedDocumentField
from datetime import datetime

class Response(EmbeddedDocument):
    responder_id = IntField(required=True)  # ID staf yang merespon
    message = StringField(required=True, max_length=1024)
    timestamp = DateTimeField(default=datetime.utcnow)

class SupportTicket(Document):
    ticket_number = StringField(required=True, unique=True, max_length=50)
    user_id = IntField(required=True)
    subject = StringField(required=True, max_length=255)
    description = StringField(required=True)
    CATEGORY_CHOICES = (
        ('Teknis', 'Teknis'),
        ('Akun', 'Akun'),
        ('Pembayaran', 'Pembayaran'),
    )
    STATUS_CHOICES = (
        ('Baru', 'Baru'),
        ('Dalam Proses', 'Dalam Proses'),
        ('Selesai', 'Selesai'),
    )
    PRIORITY_CHOICES = (
        ('Rendah', 'Rendah'),
        ('Menengah', 'Menengah'),
        ('Tinggi', 'Tinggi'),
    )
    category = StringField(required=True, choices=CATEGORY_CHOICES)
    status = StringField(required=True, choices=STATUS_CHOICES, default='Baru')
    priority = StringField(required=True, choices=PRIORITY_CHOICES, default='Menengah')
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    assigned_to = IntField(required=False, default=None)
    responses = ListField(EmbeddedDocumentField(Response))

    meta = {
        'collection': 'support_tickets',
        'indexes': ['ticket_number', 'user_id', 'status', 'priority', 'assigned_to', 'created_at', 'updated_at']
    }

    def __str__(self):
        return f"SupportTicket {self.ticket_number} - {self.status}"
