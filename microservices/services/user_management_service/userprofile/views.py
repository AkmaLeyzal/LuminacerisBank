# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from .models import UserProfile, UserDocument
from .serializers import UserProfileSerializer, UserDocumentSerializer
from .services import UserProfileService
import logging

logger = logging.getLogger(__name__)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    service = UserProfileService()

    def create(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        if not user_id:
            return Response(
                {"error": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Add user_id to context for validation
            serializer = self.get_serializer(
                data=request.data,
                context={'request': request, 'user_id': user_id}
            )
            serializer.is_valid(raise_exception=True)
            
            # Create profile using service
            profile = self.service.create_user_profile(user_id, serializer.validated_data)
            
            return Response(
                self.get_serializer(profile).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating profile: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserDocumentViewSet(viewsets.ModelViewSet):
    queryset = UserDocument.objects.all()
    serializer_class = UserDocumentSerializer
    permission_classes = [IsAuthenticated]