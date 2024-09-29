# services/account_service/account/views.py

from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Account
from .serializers import AccountSerializer

class AccountListCreateView(generics.ListCreateAPIView):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)

class AccountDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'account_number'

    def get_queryset(self):
        return Account.objects.filter(user_id=self.request.user.id)
