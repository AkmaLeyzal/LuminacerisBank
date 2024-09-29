# services/loan_service/loan/urls.py

from django.urls import path
from .views import LoanApplicationCreateView, LoanApplicationListView, LoanApplicationDetailView

urlpatterns = [
    path('loans/', LoanApplicationListView.as_view(), name='loan_list'),
    path('loans/apply/', LoanApplicationCreateView.as_view(), name='loan_apply'),
    path('loans/<str:loan_reference>/', LoanApplicationDetailView.as_view(), name='loan_detail'),
]
