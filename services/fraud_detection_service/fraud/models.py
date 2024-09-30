# services/fraud_detection_service/fraud/models.py

from django.db import models
from mongoengine import Document, fields

class FraudAlert(Document):
    transaction_id = fields.StringField(required=True)
    user_id = fields.IntField(required=True)
    risk_score = fields.FloatField(required=True)
    alert_level = fields.StringField(required=True, choices=['Low', 'Medium', 'High'])
    status = fields.StringField(required=True, choices=['New', 'Reviewed', 'Resolved'], default='New')
    created_at = fields.DateTimeField(required=True)
    updated_at = fields.DateTimeField()
    details = fields.DictField()
