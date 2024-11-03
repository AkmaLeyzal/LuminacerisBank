# support_service/support/models.py
from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime

class Comment(EmbeddedDocument):
    comment_id = fields.UUIDField(required=True)
    user_id = fields.IntField(required=True)
    user_type = fields.StringField(choices=['CUSTOMER', 'AGENT', 'SUPERVISOR'])
    content = fields.StringField(required=True)
    attachments = fields.ListField(fields.DictField())
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    is_internal = fields.BooleanField(default=False)

class SupportTicket(Document):
    ticket_number = fields.StringField(required=True, unique=True)
    user_id = fields.IntField(required=True)
    category = fields.StringField(required=True, choices=[
        'ACCOUNT', 'TRANSACTION', 'CARD', 'LOAN',
        'TECHNICAL', 'FRAUD', 'COMPLAINT', 'INQUIRY'
    ])
    subcategory = fields.StringField()
    priority = fields.StringField(choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
    status = fields.StringField(choices=[
        'OPEN', 'ASSIGNED', 'IN_PROGRESS', 'PENDING_CUSTOMER',
        'PENDING_THIRD_PARTY', 'RESOLVED', 'CLOSED', 'REOPENED'
    ])
    
    # Ticket details
    title = fields.StringField(required=True)
    description = fields.StringField(required=True)
    attachments = fields.ListField(fields.DictField())
    
    # Assignment
    assigned_to = fields.IntField()  # Agent ID
    assigned_team = fields.StringField()
    escalated_to = fields.IntField()  # Supervisor ID
    escalation_reason = fields.StringField()
    
    # SLA tracking
    sla_due_at = fields.DateTimeField()
    first_response_at = fields.DateTimeField()
    resolution_due_at = fields.DateTimeField()
    resolved_at = fields.DateTimeField()
    
    # Communication
    comments = fields.EmbeddedDocumentListField(Comment)
    last_customer_response_at = fields.DateTimeField()
    last_agent_response_at = fields.DateTimeField()
    
    # Related entities
    related_tickets = fields.ListField(fields.StringField())
    related_entities = fields.DictField()  # Like transaction_id, card_id etc
    
    # Metadata
    tags = fields.ListField(fields.StringField())
    customer_satisfaction = fields.IntField(min_value=1, max_value=5)
    feedback = fields.StringField()
    
    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    closed_at = fields.DateTimeField()

    meta = {
        'collection': 'support_tickets',
        'indexes': [
            'ticket_number',
            'user_id',
            'status',
            'assigned_to',
            'category',
            'priority',
            ('user_id', '-created_at'),
            ('assigned_to', 'status'),
            'sla_due_at'
        ]
    }

class KnowledgeBaseArticle(Document):
    title = fields.StringField(required=True)
    slug = fields.StringField(required=True, unique=True)
    content = fields.StringField(required=True)
    category = fields.StringField(required=True)
    tags = fields.ListField(fields.StringField())
    published = fields.BooleanField(default=False)
    view_count = fields.IntField(default=0)
    helpful_count = fields.IntField(default=0)
    not_helpful_count = fields.IntField(default=0)
    created_by = fields.IntField()
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'knowledge_base',
        'indexes': [
            'slug',
            'category',
            'tags',
            'published',
            '-view_count'
        ]
    }

class SupportAgent(Document):
    user_id = fields.IntField(required=True, unique=True)
    name = fields.StringField(required=True)
    email = fields.StringField(required=True)
    role = fields.StringField(choices=['AGENT', 'SUPERVISOR', 'ADMIN'])
    specialization = fields.ListField(fields.StringField())
    teams = fields.ListField(fields.StringField())
    is_available = fields.BooleanField(default=True)
    max_tickets = fields.IntField(default=10)
    current_tickets = fields.IntField(default=0)
    performance_metrics = fields.DictField()
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'support_agents',
        'indexes': [
            'user_id',
            'role',
            'is_available',
            'teams'
        ]
    }