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
    ServiceUserVerificationView
)

app_name = 'authentication'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    path('users/<int:user_id>/verification-status/', 
         UserVerificationStatusView.as_view(), 
         name='user-verification-status'),
    
    # Internal service endpoint
    path('internal/users/<int:user_id>/verify/', 
         ServiceUserVerificationView.as_view(), 
         name='service-user-verification'),
]