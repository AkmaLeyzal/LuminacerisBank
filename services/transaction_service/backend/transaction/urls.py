# services/transaction_service/transaction/urls.py

from django.urls import path
from .views import TransactionCreateView, TransactionListView

urlpatterns = [
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/create/', TransactionCreateView.as_view(), name='transaction_create'),
]
