# services/payment_service/payment/views.py

from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Payment
from .serializers import PaymentSerializer
import uuid

class PaymentCreateView(generics.CreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(
            payment_reference=str(uuid.uuid4()),
            status='Scheduled',
            account_id=self.request.data.get('account_id'),
        )
        # Tambahkan logika untuk menjadwalkan pembayaran

class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Mendapatkan pembayaran yang terkait dengan pengguna
        # Asumsikan kita memiliki mekanisme untuk mendapatkan account_id dari user_id
        return Payment.objects.filter(account_id__in=self.get_user_accounts())

    def get_user_accounts(self):
        # Implementasikan fungsi untuk mendapatkan daftar account_id milik pengguna
        return []
