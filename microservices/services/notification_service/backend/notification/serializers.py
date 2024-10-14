# services/notification_service/notification/serializers.py

from rest_framework_mongoengine import serializers
from .models import Notification

class NotificationSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
