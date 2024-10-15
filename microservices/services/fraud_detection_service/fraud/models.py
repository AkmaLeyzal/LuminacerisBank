# services/fraud_detection_service/fraud/models.py

from mongoengine import Document, IntField, DecimalField, StringField, DateTimeField, DictField
from datetime import datetime

class FraudAlert(Document):
    transaction_id = IntField(required=True)
    user_id = IntField(required=True)
    risk_score = DecimalField(required=True, precision=2, min_value=0, max_value=100)
    ALERT_LEVEL_CHOICES = (
        ('Rendah', 'Rendah'),
        ('Sedang', 'Sedang'),
        ('Tinggi', 'Tinggi'),
    )
    ALERT_STATUS_CHOICES = (
        ('Baru', 'Baru'),
        ('Ditinjau', 'Ditinjau'),
        ('Diselesaikan', 'Diselesaikan'),
    )
    alert_level = StringField(required=True, choices=ALERT_LEVEL_CHOICES)
    status = StringField(required=True, choices=ALERT_STATUS_CHOICES)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    details = DictField()

    meta = {
        'collection': 'fraud_alerts',
        'indexes': ['transaction_id', 'user_id', 'risk_score', 'alert_level', 'status', 'created_at', 'updated_at']
    }

    def __str__(self):
        return f"FraudAlert {self.transaction_id} - {self.alert_level}"
