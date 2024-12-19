# notification/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
import logging
from .models import (
    NotificationTemplate, UserNotificationSettings,
    Notification, NotificationBatch
)
from .serializers import (
    NotificationTemplateSerializer,
    UserNotificationSettingsSerializer,
    NotificationSerializer,
    NotificationBatchSerializer,
    NotificationCreateSerializer,
    NotificationBatchCreateSerializer,
    NotificationPreferenceUpdateSerializer,
    NotificationListRequestSerializer,
    NotificationCountSerializer,
    BulkNotificationStatusSerializer
)
from .services import NotificationService

logger = logging.getLogger(__name__)

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = IsAuthenticated
    service = NotificationService()

    def get_queryset(self):
        """Filter notifications based on user and parameters"""
        queryset = Notification.objects.filter(user_id=self.request.user.id)
        
        # Apply filters from query params
        filters = NotificationListRequestSerializer(data=self.request.query_params)
        if filters.is_valid():
            data = filters.validated_data

            if type := data.get('type'):
                queryset = queryset.filter(type=type)
            if data.get('read') is not None:
                queryset = queryset.filter(read=data['read'])
            if start_date := data.get('start_date'):
                queryset = queryset.filter(created_at__gte=start_date)
            if end_date := data.get('end_date'):
                queryset = queryset.filter(created_at__lte=end_date)
            if category := data.get('category'):
                queryset = queryset.filter(category=category)
            if reference_id := data.get('reference_id'):
                queryset = queryset.filter(reference_id=reference_id)

        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        try:
            counts = self.service.get_unread_count(request.user.id)
            serializer = NotificationCountSerializer(counts)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return Response(
                {'error': 'Failed to get unread count'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        try:
            notification = self.service.mark_as_read(pk, request.user.id)
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return Response(
                {'error': 'Failed to mark notification as read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        try:
            notifications = Notification.objects.filter(
                user_id=request.user.id,
                read=False
            )
            for notification in notifications:
                notification.mark_as_read()
            return Response({'status': 'success'})
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return Response(
                {'error': 'Failed to mark notifications as read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Update status for multiple notifications"""
        serializer = BulkNotificationStatusSerializer(data=request.data)
        if serializer.is_valid():
            try:
                notifications = Notification.objects.filter(
                    id__in=serializer.validated_data['notification_ids'],
                    user_id=request.user.id
                )
                
                if serializer.validated_data['status'] == 'READ':
                    for notification in notifications:
                        notification.mark_as_read()
                
                return Response({'status': 'success'})
            except Exception as e:
                logger.error(f"Error in bulk update: {str(e)}")
                return Response(
                    {'error': 'Failed to update notifications'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class UserNotificationSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = UserNotificationSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserNotificationSettings.objects.filter(
            user_id=self.request.user.id
        )

    def get_object(self):
        try:
            return UserNotificationSettings.objects.get(
                user_id=self.request.user.id
            )
        except UserNotificationSettings.DoesNotExist:
            return None

    def create(self, request):
        """Create or update user notification settings"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=True
            )
            
            if serializer.is_valid():
                if instance:
                    serializer.update(instance, serializer.validated_data)
                else:
                    serializer.save(user_id=request.user.id)
                return Response(serializer.data)
                
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            return Response(
                {'error': 'Failed to update notification settings'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['patch'])
    def update_preferences(self, request):
        """Update notification preferences"""
        serializer = NotificationPreferenceUpdateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                settings = self.get_object()
                if not settings:
                    return Response(
                        {'error': 'Settings not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Update specific preference
                updated = False
                for pref in settings.preferences:
                    if pref.channel == serializer.validated_data['channel']:
                        pref.enabled = serializer.validated_data['enabled']
                        pref.quiet_hours_start = serializer.validated_data.get('quiet_hours_start')
                        pref.quiet_hours_end = serializer.validated_data.get('quiet_hours_end')
                        pref.frequency = serializer.validated_data.get('frequency', 'IMMEDIATE')
                        updated = True
                        break

                if not updated:
                    settings.preferences.append(NotificationPreference(
                        **serializer.validated_data
                    ))

                settings.save()
                return Response(
                    UserNotificationSettingsSerializer(settings).data
                )

            except Exception as e:
                logger.error(f"Error updating preferences: {str(e)}")
                return Response(
                    {'error': 'Failed to update preferences'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['post'])
    def mute_category(self, request):
        """Mute notifications for specific category"""
        category = request.data.get('category')
        if not category:
            return Response(
                {'error': 'Category is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            settings = self.get_object()
            if not settings:
                return Response(
                    {'error': 'Settings not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            if category not in settings.categories_muted:
                settings.categories_muted.append(category)
                settings.save()

            return Response(
                UserNotificationSettingsSerializer(settings).data
            )

        except Exception as e:
            logger.error(f"Error muting category: {str(e)}")
            return Response(
                {'error': 'Failed to mute category'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = IsAuthenticated

    def perform_create(self, serializer):
        """Create new template version"""
        existing = NotificationTemplate.objects.filter(
            name=serializer.validated_data['name']
        ).order_by('-version').first()

        version = 1
        if existing:
            version = existing.version + 1

        serializer.save(
            version=version,
            created_by=str(self.request.user.id)
        )

class NotificationBatchViewSet(viewsets.ModelViewSet):
    queryset = NotificationBatch.objects.all()
    serializer_class = NotificationBatchSerializer
    permission_classes = IsAuthenticated
    service = NotificationService()

    def create(self, request):
        """Create new notification batch"""
        serializer = NotificationBatchCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                batch = self.service.create_batch(
                    batch_data=serializer.validated_data,
                    created_by=request.user.id
                )
                return Response(
                    NotificationBatchSerializer(batch).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"Error creating batch: {str(e)}")
                return Response(
                    {'error': 'Failed to create notification batch'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a scheduled batch"""
        try:
            batch = self.get_object()
            if batch.status not in ['DRAFT', 'SCHEDULED']:
                return Response(
                    {'error': 'Can only cancel draft or scheduled batches'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            batch.status = 'CANCELLED'
            batch.save()
            return Response(NotificationBatchSerializer(batch).data)

        except Exception as e:
            logger.error(f"Error cancelling batch: {str(e)}")
            return Response(
                {'error': 'Failed to cancel batch'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )