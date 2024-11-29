# accounts/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from .services import AccountService
from .serializers import (
    BankAccountSerializer,
    AccountCreateSerializer,
    AccountStatusUpdateSerializer,
    AccountHoldAmountSerializer
)
from .cache.decorators import cache_account_details, invalidate_account_cache

class BankAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for bank account operations"""
    permission_classes = [IsAuthenticated]
    serializer_class = BankAccountSerializer
    service = AccountService()

    def get_queryset(self):
        """Filter accounts for current user"""
        return self.service.get_user_accounts(self.request.user.id)

    @cache_account_details()
    def retrieve(self, request, pk=None):
        """Get account details"""
        try:
            details = self.service.get_account_details(pk)
            return Response(details)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request):
        """Create new bank account"""
        try:
            serializer = AccountCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            account = self.service.create_account(
                user_id=request.user.id,
                **serializer.validated_data
            )
            
            response_serializer = BankAccountSerializer(account)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['put'])
    @invalidate_account_cache
    def status(self, request, pk=None):
        """Update account status"""
        try:
            serializer = AccountStatusUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            result = self.service.update_account_status(
                account_id=pk,
                **serializer.validated_data
            )
            
            return Response(result)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    @invalidate_account_cache
    def hold(self, request, pk=None):
        """Place hold on account balance"""
        try:
            serializer = AccountHoldAmountSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            result = self.service.place_hold_amount(
                account_id=pk,
                **serializer.validated_data
            )
            
            return Response(result)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )