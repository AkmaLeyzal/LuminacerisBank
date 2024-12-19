# notification/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet,
    UserNotificationSettingsViewSet,
    NotificationTemplateViewSet,
    NotificationBatchViewSet
)

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(
    r'notification-settings',
    UserNotificationSettingsViewSet,
    basename='notification-settings'
)
router.register(
    r'notification-templates',
    NotificationTemplateViewSet,
    basename='notification-templates'
)
router.register(
    r'notification-batches',
    NotificationBatchViewSet,
    basename='notification-batches'
)

urlpatterns = [
    path('api/', include(router.urls)),
    
    # Custom notification endpoints
    path(
        'api/notifications/unread-count/',
        NotificationViewSet.as_view({'get': 'unread_count'}),
        name='notification-unread-count'
    ),
    
    path(
        'api/notifications/<str:pk>/mark-read/',
        NotificationViewSet.as_view({'post': 'mark_read'}),
        name='notification-mark-read'
    ),
    
    path(
        'api/notifications/mark-all-read/',
        NotificationViewSet.as_view({'post': 'mark_all_read'}),
        name='notification-mark-all-read'
    ),
    
    path(
        'api/notifications/bulk-update/',
        NotificationViewSet.as_view({'post': 'bulk_update'}),
        name='notification-bulk-update'
    ),
    
    # Settings endpoints
    path(
        'api/notification-settings/update-preferences/',
        UserNotificationSettingsViewSet.as_view({'patch': 'update_preferences'}),
        name='notification-update-preferences'
    ),
    
    path(
        'api/notification-settings/mute-category/',
        UserNotificationSettingsViewSet.as_view({'post': 'mute_category'}),
        name='notification-mute-category'
    ),
    
    # Batch endpoints
    path(
        'api/notification-batches/<str:pk>/cancel/',
        NotificationBatchViewSet.as_view({'post': 'cancel'}),
        name='notification-batch-cancel'
    ),
]

# Available endpoints:
# GET    /api/notifications/                 - List all notifications
# POST   /api/notifications/                 - Create notification
# GET    /api/notifications/{id}/            - Get notification details
# GET    /api/notifications/unread-count/    - Get unread count
# POST   /api/notifications/{id}/mark-read/  - Mark as read
# POST   /api/notifications/mark-all-read/   - Mark all as read
# POST   /api/notifications/bulk-update/     - Bulk update notifications

# GET    /api/notification-settings/         - Get user settings
# POST   /api/notification-settings/         - Create/Update settings
# PATCH  /api/notification-settings/update-preferences/ - Update preferences
# POST   /api/notification-settings/mute-category/     - Mute category

# GET    /api/notification-templates/        - List templates
# POST   /api/notification-templates/        - Create template
# GET    /api/notification-templates/{id}/   - Get template details

# GET    /api/notification-batches/          - List batches
# POST   /api/notification-batches/          - Create batch
# GET    /api/notification-batches/{id}/     - Get batch details
# POST   /api/notification-batches/{id}/cancel/ - Cancel batch