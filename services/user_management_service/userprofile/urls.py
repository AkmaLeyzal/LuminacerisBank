# services/user_management_service/userprofile/urls.py

from django.urls import path
from .views import UserProfileView

urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]
