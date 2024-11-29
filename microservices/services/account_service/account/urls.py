# accounts/urls.py

# from django.urls import path
# from rest_framework.routers import DefaultRouter
# from .views import (
#     BankAccountViewSet,
#     AccountBalanceLogView,
#     AccountStatusView,
#     AccountMetricsView
# )

# router = DefaultRouter()
# router.register(r'account', BankAccountViewSet, basename='account')

# urlpatterns = [
#     path('<str:account_id>/logs/', 
#          AccountBalanceLogView.as_view(), 
#          name='account-logs'),
#     path('<str:account_id>/status/', 
#          AccountStatusView.as_view(), 
#          name='account-status'),
#     path('metrics/', 
#          AccountMetricsView.as_view(), 
#          name='account-metrics'),
# ] + router.urls

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BankAccountViewSet

router = DefaultRouter()
router.register(r'accounts', BankAccountViewSet, basename='account')

urlpatterns = [
    path('', include(router.urls)),
]