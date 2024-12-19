# transaction/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from .models import Transaction, TransactionDetail
from .serializers import (
    TransactionSerializer,
    TransferRequestSerializer,
    TransactionStatusSerializer,
    TransactionListRequestSerializer,
    ReverseTransactionSerializer
)
from .services import TransactionService
import logging

logger = logging.getLogger(__name__)

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    service = TransactionService()

    @action(detail=False, methods=['post'])
    def transfer(self, request):
        """Initiate a new transfer transaction"""
        serializer = TransferRequestSerializer(
            data=request.data,
            context={'sender_account_id': request.user.account_id}
        )

        if serializer.is_valid():
            try:
                # Get request information
                request_info = {
                    'user_id': str(request.user.id),
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT'),
                    'device_id': request.headers.get('X-Device-ID'),
                    'session_id': request.headers.get('X-Session-ID'),
                    'auth_token_jti': request.auth['jti'] if request.auth else None
                }

                # Initiate transfer
                transaction = self.service.initiate_transfer(
                    sender_account_id=request.user.account_id,
                    data=serializer.validated_data,
                    request_info=request_info
                )

                response_serializer = TransactionSerializer(transaction)
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )

            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Transfer error: {str(e)}")
                return Response(
                    {'error': 'Transfer failed. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get transaction status"""
        try:
            status_info = self.service.get_transaction_status(pk)
            serializer = TransactionStatusSerializer(status_info)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error fetching transaction status: {str(e)}")
            return Response(
                {'error': 'Unable to fetch transaction status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def reverse(self, request, pk=None):
        """Reverse a transaction"""
        try:
            original_transaction = Transaction.objects.get(pk=pk)
            serializer = ReverseTransactionSerializer(
                data=request.data,
                context={'original_transaction': original_transaction}
            )

            if serializer.is_valid():
                reversal = self.service.reverse_transaction(
                    transaction_id=pk,
                    reason=serializer.validated_data['reason'],
                    reversal_amount=serializer.validated_data.get('reversal_amount')
                )

                response_serializer = TransactionSerializer(reversal)
                return Response(response_serializer.data)

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error reversing transaction: {str(e)}")
            return Response(
                {'error': 'Unable to process reversal'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_queryset(self):
        """Filter transactions based on request parameters"""
        queryset = Transaction.objects.filter(is_active=True)
        
        # Get filter parameters
        filters = TransactionListRequestSerializer(
            data=self.request.query_params
        )
        if not filters.is_valid():
            return queryset

        data = filters.validated_data

        # Apply filters
        if account_id := data.get('account_id'):
            queryset = queryset.filter(
                Q(sender_account_id=account_id) | 
                Q(receiver_account_id=account_id)
            )

        if transaction_type := data.get('transaction_type'):
            queryset = queryset.filter(transaction_type=transaction_type)

        if status_filter := data.get('status'):
            queryset = queryset.filter(status=status_filter)

        if start_date := data.get('start_date'):
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date := data.get('end_date'):
            queryset = queryset.filter(created_at__lte=end_date)

        if min_amount := data.get('min_amount'):
            queryset = queryset.filter(amount__gte=min_amount)

        if max_amount := data.get('max_amount'):
            queryset = queryset.filter(amount__lte=max_amount)

        return queryset.order_by('-created_at')