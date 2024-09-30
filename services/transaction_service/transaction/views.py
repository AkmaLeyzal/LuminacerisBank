# services/transaction_service/transaction/views.py

from django.shortcuts import render
from rest_framework import generics, permissions, status
from .models import Transaction
from .serializers import TransactionSerializer
from rest_framework.response import Response
import uuid
from kafka import KafkaProducer
import json
import os

producer = KafkaProducer(
    bootstrap_servers=os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

class TransactionCreateView(generics.CreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        transaction = serializer.save(
            transaction_reference=str(uuid.uuid4()),
            status='Pending',
            # Logika tambahan seperti validasi saldo
        )
        # Mengirim pesan ke Kafka
        producer.send('transactions', {
            'transaction_reference': transaction.transaction_reference,
            'from_account_id': transaction.from_account_id,
            'to_account_id': transaction.to_account_id,
            'amount': str(transaction.amount),
            'currency': transaction.currency,
            'transaction_type': transaction.transaction_type,
            'transaction_date': str(transaction.transaction_date),
            'user_id': self.request.user.id,
            # Field tambahan jika diperlukan
        })

class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Mendapatkan transaksi yang terkait dengan pengguna
        user_id = self.request.user.id
        return Transaction.objects.filter(from_account_id=user_id) | Transaction.objects.filter(to_account_id=user_id)

