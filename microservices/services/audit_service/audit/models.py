# audit_service/audit/models.py
from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime

class AuditLog(Document):
    event_id = fields.UUIDField(required=True, unique=True)
    timestamp = fields.DateTimeField(default=datetime.utcnow)
    service = fields.StringField(required=True)
    action = fields.StringField(required=True)
    status = fields.StringField(choices=['SUCCESS', 'FAILURE', 'WARNING'])
    
    # User information
    user_id = fields.IntField()
    user_email = fields.StringField()
    user_role = fields.StringField()
    
    # Request details
    ip_address = fields.StringField()
    user_agent = fields.StringField()
    request_method = fields.StringField()
    request_path = fields.StringField()
    request_body = fields.DictField()
    
    # Change tracking
    resource_type = fields.StringField()
    resource_id = fields.StringField()
    old_value = fields.DictField()
    new_value = fields.DictField()
    
    # Additional context
    correlation_id = fields.StringField()
    session_id = fields.StringField()
    geo_location = fields.PointField()
    device_info = fields.DictField()
    
    # Error details
    error_code = fields.StringField()
    error_message = fields.StringField()
    stack_trace = fields.StringField()

    meta = {
        'collection': 'audit_logs',
        'indexes': [
            {'fields': ['-timestamp']},
            {'fields': ['user_id', '-timestamp']},
            {'fields': ['service', 'action']},
            {'fields': ['resource_type', 'resource_id']},
            {'fields': ['correlation_id']},
            {'fields': ['ip_address', '-timestamp']}
        ]
    }

class SecurityAuditLog(Document):
    event_id = fields.UUIDField(required=True, unique=True)
    timestamp = fields.DateTimeField(default=datetime.utcnow)
    event_type = fields.StringField(required=True, choices=[
        'LOGIN', 'LOGOUT', 'PASSWORD_CHANGE', 'MFA_ENABLE',
        'MFA_DISABLE', 'ACCESS_DENIED', 'PERMISSION_CHANGE',
        'TOKEN_REFRESH', 'TOKEN_REVOKE'
    ])
    
    # User details
    user_id = fields.IntField()
    user_email = fields.StringField()
    user_role = fields.StringField()
    
    # Security context
    ip_address = fields.StringField()
    user_agent = fields.StringField()
    device_id = fields.StringField()
    location = fields.PointField()
    
    # Event details
    status = fields.StringField(choices=['SUCCESS', 'FAILURE'])
    failure_reason = fields.StringField()
    auth_method = fields.StringField()
    session_id = fields.StringField()
    
    # Risk assessment
    risk_score = fields.FloatField()
    risk_factors = fields.ListField(fields.StringField())
    is_suspicious = fields.BooleanField()

    meta = {
        'collection': 'security_audit_logs',
        'indexes': [
            {'fields': ['-timestamp']},
            {'fields': ['user_id', '-timestamp']},
            {'fields': ['event_type']},
            {'fields': ['ip_address']},
            {'fields': ['is_suspicious']},
            {'fields': ['device_id']}
        ]
    }

class DataAccessLog(Document):
    event_id = fields.UUIDField(required=True, unique=True)
    timestamp = fields.DateTimeField(default=datetime.utcnow)
    user_id = fields.IntField(required=True)
    action = fields.StringField(required=True, choices=[
        'VIEW', 'EXPORT', 'MODIFY', 'DELETE'
    ])
    
    # Data access details
    data_type = fields.StringField(required=True)
    data_id = fields.StringField()
    fields_accessed = fields.ListField(fields.StringField())
    query_parameters = fields.DictField()
    
    # Access context
    service = fields.StringField()
    endpoint = fields.StringField()
    ip_address = fields.StringField()
    user_agent = fields.StringField()
    
    # Compliance
    purpose = fields.StringField()
    legal_basis = fields.StringField()
    retention_period = fields.IntField()
    
    # Security
    encryption_status = fields.BooleanField()
    data_classification = fields.StringField()
    sensitivity_level = fields.StringField()

    meta = {
        'collection': 'data_access_logs',
        'indexes': [
            {'fields': ['-timestamp']},
            {'fields': ['user_id', '-timestamp']},
            {'fields': ['data_type', 'data_id']},
            {'fields': ['action']},
            {'fields': ['sensitivity_level']}
        ]
    }