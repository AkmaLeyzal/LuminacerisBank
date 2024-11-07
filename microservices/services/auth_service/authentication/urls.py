from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    TokenRefreshView,
    RegisterView
)
# from .views.metadata import MetadataView 

urlpatterns = [
    # Auth endpoints
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    
    # Service metadata
    # path('metadata/', MetadataView.as_view(), name='auth-metadata'),
    # path('health/', HealthCheckView.as_view(), name='auth-health'),
]