# Middleware di setiap service yang mengirim log
# services/any_service/any_app/middleware.py

import json
from kafka import KafkaProducer
from django.utils.deprecation import MiddlewareMixin
import os

producer = KafkaProducer(
    bootstrap_servers=os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

class AuditMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        log = {
            'user_id': request.user.id if request.user.is_authenticated else None,
            'action': request.method,
            'resource': request.path,
            'timestamp': str(datetime.utcnow()),
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'status_code': response.status_code,
            'request_data': request.POST.dict(),
            'response_data': response.data if hasattr(response, 'data') else {},
            'error_message': response.status_text if response.status_code >= 400 else '',
        }
        producer.send('audit_logs', log)
        return response
