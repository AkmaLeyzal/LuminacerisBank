# services/fraud_detection_service/fraud/consumer.py

from kafka_cloud import KafkaConsumer
import json
from .models import FraudAlert
from datetime import datetime

consumer = KafkaConsumer(
    'transactions',
    bootstrap_servers='kafka:9092',
    auto_offset_reset='earliest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

def detect_fraud(transaction):
    # Implementasikan logika deteksi penipuan
    risk_score = 0
    if transaction['amount'] > 10000:
        risk_score += 50
    # Tambahkan aturan lainnya
    return risk_score

for message in consumer:
    transaction = message.value
    risk_score = detect_fraud(transaction)
    if risk_score >= 50:
        FraudAlert(
            transaction_id=transaction['transaction_reference'],
            user_id=transaction['user_id'],
            risk_score=risk_score,
            alert_level='High' if risk_score >= 80 else 'Medium',
            status='New',
            created_at=datetime.utcnow(),
            details=transaction
        ).save()
        # Kirim notifikasi jika diperlukan
