# services/notification_service/notification/views.py

from django.shortcuts import render
from rest_framework_mongoengine import generics
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework import permissions

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects(user_id=self.request.user.id)
