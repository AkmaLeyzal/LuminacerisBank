# notification/serializers.py
from rest_framework import serializers
from .models import (
    NotificationTemplate, UserNotificationSettings,
    Notification, NotificationBatch, NotificationPreference,
    UserDevice
)

class NotificationPreferenceSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=['EMAIL', 'SMS', 'PUSH', 'IN_APP'])
    enabled = serializers.BooleanField(default=True)
    quiet_hours_start = serializers.IntegerField(min_value=0, max_value=23, required=False)
    quiet_hours_end = serializers.IntegerField(min_value=0, max_value=23, required=False)
    frequency = serializers.ChoiceField(
        choices=['IMMEDIATE', 'DAILY_DIGEST', 'WEEKLY_DIGEST'],
        default='IMMEDIATE'
    )

class UserDeviceSerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True)
    device_type = serializers.ChoiceField(choices=['IOS', 'ANDROID', 'WEB'])
    push_token = serializers.CharField(required=False)
    is_active = serializers.BooleanField(default=True)
    last_used = serializers.DateTimeField(read_only=True)

class UserNotificationSettingsSerializer(serializers.DocumentSerializer):
    preferences = NotificationPreferenceSerializer(many=True)
    devices = UserDeviceSerializer(many=True)

    class Meta:
        model = UserNotificationSettings
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class NotificationTemplateSerializer(serializers.DocumentSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'version']

class NotificationSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = [
            'created_at', 'sent_at', 'read_at',
            'delivery_attempts', 'status'
        ]

class NotificationCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=True)
    notification_type = serializers.ChoiceField(choices=[
        'TRANSACTION', 'SECURITY', 'ACCOUNT', 'MARKETING',
        'SYSTEM', 'FRAUD_ALERT', 'PAYMENT', 'LOAN'
    ])
    priority = serializers.ChoiceField(choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
    title = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    template_name = serializers.CharField(required=False)
    channels = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    metadata = serializers.DictField(required=False)
    category = serializers.CharField(required=False)
    action_url = serializers.URLField(required=False)
    scheduled_at = serializers.DateTimeField(required=False)
    expires_at = serializers.DateTimeField(required=False)
    reference_id = serializers.CharField(required=False)
    reference_type = serializers.CharField(required=False)

class NotificationBatchSerializer(serializers.DocumentSerializer):
    class Meta:
        model = NotificationBatch
        fields = '__all__'
        read_only_fields = [
            'created_at', 'started_at', 'completed_at',
            'processed_count', 'failed_count'
        ]

class NotificationBatchCreateSerializer(serializers.Serializer):
    template_name = serializers.CharField(required=True)
    notification_batch_type = serializers.CharField(required=True)
    title = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    user_filter = serializers.DictField(required=False)
    priority = serializers.ChoiceField(
        choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        default='LOW'
    )
    channels = serializers.ListField(child=serializers.CharField())
    metadata = serializers.DictField(required=False)
    category = serializers.CharField(required=False)
    action_url = serializers.URLField(required=False)
    scheduled_at = serializers.DateTimeField(required=False)
    expires_at = serializers.DateTimeField(required=False)

class NotificationUpdateSerializer(serializers.Serializer):
    read = serializers.BooleanField(required=False)

class NotificationListRequestSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=True)
    notification_list_type = serializers.CharField(required=False)
    read = serializers.BooleanField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)
    category = serializers.CharField(required=False)
    reference_id = serializers.CharField(required=False)

    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError(
                    "End date must be after start date"
                )
        return data

class NotificationCountSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()
    categories = serializers.DictField(child=serializers.IntegerField())

class NotificationPreferenceUpdateSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(
        choices=['EMAIL', 'SMS', 'PUSH', 'IN_APP'],
        required=True
    )
    enabled = serializers.BooleanField(required=True)
    quiet_hours_start = serializers.IntegerField(
        min_value=0,
        max_value=23,
        required=False,
        allow_null=True
    )
    quiet_hours_end = serializers.IntegerField(
        min_value=0,
        max_value=23,
        required=False,
        allow_null=True
    )
    frequency = serializers.ChoiceField(
        choices=['IMMEDIATE', 'DAILY_DIGEST', 'WEEKLY_DIGEST'],
        required=False,
        default='IMMEDIATE'
    )

class BulkNotificationStatusSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )
    status = serializers.ChoiceField(
        choices=['READ', 'UNREAD', 'ARCHIVED'],
        required=True
    )