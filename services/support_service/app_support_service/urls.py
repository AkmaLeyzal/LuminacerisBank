# services/support_service/support/urls.py

from django.urls import path
from .views import SupportTicketCreateView, SupportTicketListView

urlpatterns = [
    path('support/tickets/', SupportTicketListView.as_view(), name='support_ticket_list'),
    path('support/tickets/create/', SupportTicketCreateView.as_view(), name='support_ticket_create'),
]
