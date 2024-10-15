# services/support_service/support/views.py

from django.shortcuts import render
from rest_framework_mongoengine import generics
from .models import SupportTicket
from .serializers import SupportTicketSerializer
from rest_framework import permissions
import uuid

class SupportTicketCreateView(generics.CreateAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)

class SupportTicketListView(generics.ListAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SupportTicket.objects(user_id=self.request.user.id)
