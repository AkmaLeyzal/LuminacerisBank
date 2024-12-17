# user_management/urls.py (App Level URLs)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet,
    UserDocumentViewSet,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet)
router.register(r'documents', UserDocumentViewSet)

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom User Profile endpoints
    path('users/<uuid:user_id>/profile/', 
         UserProfileViewSet.as_view({
            #  'get': 'retrieve_by_user',
             'post': 'create',
             'put': 'update',
             'patch': 'partial_update'
         })),
    
    # User Documents endpoints
    path('users/<uuid:user_id>/documents/', 
         UserDocumentViewSet.as_view({
             'get': 'list_user_documents',
             'post': 'create_user_document'
         })),
         
    # Profile verification
    path('profiles/<uuid:profile_id>/verify/', 
         UserProfileViewSet.as_view({'post': 'verify_profile'})),
         
    # Document verification
    path('documents/<uuid:document_id>/verify/', 
         UserDocumentViewSet.as_view({'post': 'verify_document'}))]