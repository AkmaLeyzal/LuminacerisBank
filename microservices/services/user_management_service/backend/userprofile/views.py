# services/user_management_service/userprofile/views.py

from django.shortcuts import render
from rest_framework import generics, permissions
from .models import UserProfile
from .serializers import UserProfileSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user_id = self.request.user.id 
        profile, created = UserProfile.objects.get_or_create(user_id=user_id)
        return profile

