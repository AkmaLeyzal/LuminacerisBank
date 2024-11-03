# microservices/services/auth_service/authentication/urls.py
from django.urls import path
from .views import (
    LoginView, RegisterView, 
    LogoutView, ChangePasswordView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]