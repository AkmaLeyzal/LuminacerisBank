# services/support_service/support/serializers.py

from rest_framework_mongoengine import serializers
from .models import SupportTicket, Response

class ResponseSerializer(serializers.EmbeddedDocumentSerializer):
    class Meta:
        model = Response
        fields = '__all__'

class SupportTicketSerializer(serializers.DocumentSerializer):
    responses = ResponseSerializer(many=True, required=False)

    class Meta:
        model = SupportTicket
        fields = '__all__'
        read_only_fields = ('ticket_number', 'status', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['ticket_number'] = str(uuid.uuid4())
        return super().create(validated_data)
