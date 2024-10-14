# services/card_management_service/card/urls.py

from django.urls import path
from .views import CardCreateView, CardListView

urlpatterns = [
    path('cards/', CardListView.as_view(), name='card_list'),
    path('cards/create/', CardCreateView.as_view(), name='card_create'),
]
