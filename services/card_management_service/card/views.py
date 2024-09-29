# services/card_management_service/card/views.py

from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Card
from .serializers import CardSerializer
import uuid
from hashlib import sha256

class CardCreateView(generics.CreateAPIView):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Hash CVV dan PIN sebelum disimpan
        cvv = serializer.validated_data.get('cvv')
        pin = serializer.validated_data.get('pin_hash')
        serializer.save(
            card_number=self.generate_card_number(),
            cvv=self.encrypt_value(cvv),
            pin_hash=self.encrypt_value(pin),
            cardholder_name=self.request.user.get_full_name(),
        )

    def generate_card_number(self):
        # Implementasikan logika pembuatan nomor kartu unik
        return str(uuid.uuid4().int)[:16]

    def encrypt_value(self, value):
        # Implementasikan metode enkripsi yang aman
        return sha256(value.encode('utf-8')).hexdigest()

class CardListView(generics.ListAPIView):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Mendapatkan kartu yang terkait dengan pengguna
        return Card.objects.filter(account_id__in=self.get_user_accounts())

    def get_user_accounts(self):
        # Implementasikan fungsi untuk mendapatkan daftar account_id milik pengguna
        return []
