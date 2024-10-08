# services/account_service/account/urls.py

from django.urls import path
from .views import AccountListCreateView, AccountDetailView

urlpatterns = [
    path('accounts/', AccountListCreateView.as_view(), name='account_list_create'),
    path('accounts/<str:account_number>/', AccountDetailView.as_view(), name='account_detail'),
]
