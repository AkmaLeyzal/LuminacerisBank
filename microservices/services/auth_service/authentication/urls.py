# authentication/urls.py

from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    EmailVerificationView,
    PasswordResetRequestView,
    VerifyOTPView,
    PasswordResetView,
    TokenRefreshView,
    UserVerificationStatusView,
    ServiceUserVerificationView,
    TokenVerifyView
)

app_name = 'authentication'

urlpatterns = [
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('api/auth/password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('api/auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('api/auth/password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    path('api/auth/users/<int:user_id>/verification-status/', 
         UserVerificationStatusView.as_view(), 
         name='user-verification-status'),
    
    # Internal service endpoint
    path('api/auth/internal/users/<uuid:user_id>/verify/', 
         ServiceUserVerificationView.as_view(), 
         name='service-user-verification'),

    path('api/auth/token/verify/', 
         TokenVerifyView.as_view(), 
         name='token-verify'),
]