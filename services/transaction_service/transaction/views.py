# services/transaction_service/transaction/views.py

from django.shortcuts import render
from rest_framework import generics, permissions, status
from .models import Transaction
from .serializers import TransactionSerializer
from rest_framework.response import Response
import uuid

class TransactionCreateView(generics.CreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(
            transaction_reference=str(uuid.uuid4()),
            status='Pending',
            # Tambahkan logika tambahan seperti validasi saldo, fee, dll.
        )
        # Kirim pesan ke Kafka atau proses transaksi

class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Mendapatkan transaksi yang terkait dengan pengguna
        user_id = self.request.user.id
        return Transaction.objects.filter(from_account_id=user_id) | Transaction.objects.filter(to_account_id=user_id)

