# fraud_detection_service/fraud_detection/models.py
from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime

class FraudRule(Document):
    """Rules for fraud detection"""
    name = fields.StringField(required=True, unique=True)
    description = fields.StringField()
    rule_type = fields.StringField(choices=[
        'TRANSACTION', 'LOGIN', 'DEVICE', 'LOCATION', 'BEHAVIOR'
    ])
    conditions = fields.DictField(required=True)  # Rule conditions in JSON format
    risk_score = fields.FloatField(min_value=0, max_value=100)
    is_active = fields.BooleanField(default=True)
    created_by = fields.IntField()
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'fraud_rules',
        'indexes': [
            'name',
            'rule_type',
            'is_active'
        ]
    }

class MLModel(Document):
    """Machine Learning Model Metadata"""
    model_name = fields.StringField(required=True, unique=True)
    version = fields.StringField(required=True)
    model_type = fields.StringField(choices=[
        'CLASSIFICATION', 'ANOMALY_DETECTION', 'CLUSTERING'
    ])
    features = fields.ListField(fields.StringField())
    performance_metrics = fields.DictField()
    training_date = fields.DateTimeField()
    is_active = fields.BooleanField(default=False)
    model_path = fields.StringField()
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'ml_models',
        'indexes': [
            ('model_name', 'version'),
            'is_active'
        ]
    }

class FraudAlert(Document):
    """Fraud Detection Alerts"""
    alert_id = fields.UUIDField(required=True, unique=True)
    user_id = fields.IntField(required=True)
    alert_type = fields.StringField(required=True, choices=[
        'SUSPICIOUS_TRANSACTION', 'UNUSUAL_LOGIN',
        'DEVICE_CHANGE', 'LOCATION_ANOMALY',
        'PATTERN_ANOMALY', 'RULE_BASED'
    ])
    severity = fields.StringField(choices=[
        'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    ])
    status = fields.StringField(choices=[
        'DETECTED', 'INVESTIGATING', 'CONFIRMED',
        'FALSE_POSITIVE', 'RESOLVED', 'BLOCKED'
    ])
    
    # Detection details
    detection_method = fields.StringField(choices=['RULE', 'ML', 'HYBRID'])
    detection_time = fields.DateTimeField(default=datetime.utcnow)
    risk_score = fields.FloatField(min_value=0, max_value=100)
    triggered_rules = fields.ListField(fields.StringField())
    ml_model_version = fields.StringField()
    
    # Event details
    event_type = fields.StringField()  # Type of event that triggered alert
    event_id = fields.StringField()    # ID of triggering event
    event_data = fields.DictField()    # Details of the triggering event
    
    # Location and device
    ip_address = fields.StringField()
    location = fields.PointField()
    device_info = fields.DictField()
    
    # Action taken
    action_taken = fields.StringField(choices=[
        'NONE', 'BLOCK', 'FLAG', 'NOTIFY'
    ])
    blocked_at = fields.DateTimeField()
    blocked_by = fields.StringField()
    
    # Resolution
    resolution_status = fields.StringField()
    resolution_notes = fields.StringField()
    resolved_by = fields.IntField()
    resolved_at = fields.DateTimeField()
    
    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'fraud_alerts',
        'indexes': [
            'alert_id',
            'user_id',
            'status',
            'severity',
            ('user_id', '-created_at'),
            'detection_time'
        ]
    }

class UserBehaviorProfile(Document):
    """User behavior profiling for anomaly detection"""
    user_id = fields.IntField(required=True, unique=True)
    
    # Transaction patterns
    typical_transaction_amount = fields.DictField()  # Stats by transaction type
    typical_transaction_frequency = fields.DictField()
    common_merchants = fields.ListField(fields.StringField())
    common_transaction_locations = fields.ListField(fields.PointField())
    
    # Login patterns
    usual_login_times = fields.ListField(fields.IntField())
    usual_locations = fields.ListField(fields.PointField())
    known_devices = fields.ListField(fields.DictField())
    usual_ip_addresses = fields.ListField(fields.StringField())
    
    # Risk factors
    risk_score = fields.FloatField(min_value=0, max_value=100)
    risk_factors = fields.ListField(fields.StringField())
    last_risk_assessment = fields.DateTimeField()
    
    # History
    fraud_history = fields.ListField(fields.DictField())
    alert_history = fields.ListField(fields.ReferenceField('FraudAlert'))
    
    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'user_behavior_profiles',
        'indexes': [
            'user_id',
            'risk_score',
            'updated_at'
        ]
    }

class MLPredictionLog(Document):
    """Logs for ML model predictions"""
    prediction_id = fields.UUIDField(required=True, unique=True)
    model_name = fields.StringField(required=True)
    model_version = fields.StringField(required=True)
    input_features = fields.DictField(required=True)
    prediction = fields.DictField(required=True)
    confidence_score = fields.FloatField()
    execution_time = fields.FloatField()  # in milliseconds
    alert_generated = fields.BooleanField()
    alert_id = fields.StringField()
    created_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'ml_prediction_logs',
        'indexes': [
            'prediction_id',
            'model_name',
            'alert_id',
            '-created_at'
        ]
    }