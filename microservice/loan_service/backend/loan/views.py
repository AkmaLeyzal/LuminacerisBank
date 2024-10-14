# services/loan_service/loan/views.py

from django.shortcuts import render
from rest_framework import generics, permissions
from .models import LoanApplication
from .serializers import LoanApplicationSerializer

class LoanApplicationCreateView(generics.CreateAPIView):
    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)

class LoanApplicationListView(generics.ListAPIView):
    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LoanApplication.objects.filter(user_id=self.request.user.id)

class LoanApplicationDetailView(generics.RetrieveAPIView):
    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'loan_reference'

    def get_queryset(self):
        return LoanApplication.objects.filter(user_id=self.request.user.id)
