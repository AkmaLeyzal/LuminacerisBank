# services/payment_service/payment/urls.py

from django.urls import path
from .views import PaymentCreateView, PaymentListView

urlpatterns = [
    path('payments/', PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', PaymentCreateView.as_view(), name='payment_create'),
]
