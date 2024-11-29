# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet, UserDocumentViewSet

router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet)
router.register(r'documents', UserDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Custom endpoints for user-specific operations
    path('users/<int:user_id>/profile/', 
         UserProfileViewSet.as_view({'post': 'create', 'get': 'retrieve'})),
]