# transaction/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('api/', include(router.urls)),
    
    # Custom transaction endpoints
    path('api/transactions/transfer/', 
         TransactionViewSet.as_view({'post': 'transfer'}),
         name='transaction-transfer'),
         
    path('api/transactions/<uuid:pk>/status/', 
         TransactionViewSet.as_view({'get': 'status'}),
         name='transaction-status'),
         
    path('api/transactions/<uuid:pk>/reverse/', 
         TransactionViewSet.as_view({'post': 'reverse'}),
         name='transaction-reverse'),
]

# Available endpoints:
# GET /api/transactions/ - List all transactions (with filters)
# POST /api/transactions/transfer/ - Initiate new transfer
# GET /api/transactions/{id}/ - Get transaction details
# GET /api/transactions/{id}/status/ - Get transaction status
# POST /api/transactions/{id}/reverse/ - Reverse a transaction