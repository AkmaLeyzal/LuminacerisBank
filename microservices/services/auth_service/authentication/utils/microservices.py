# authentication/utils/microservices.py

import requests
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MicroserviceClient:
    @staticmethod
    def send_request(
        service: str,
        endpoint: str,
        method: str = 'GET',
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> Dict:
        """Send request to another microservice"""
        if service not in settings.MICROSERVICES:
            raise ValueError(f"Unknown service: {service}")
            
        service_config = settings.MICROSERVICES[service]
        url = f"{service_config['base_url']}/{endpoint.lstrip('/')}"
        
        default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Internal-Request': 'true'
        }
        
        if headers:
            default_headers.update(headers)
            
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=default_headers,
                timeout=timeout or service_config['timeout']
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Microservice communication error: {str(e)}")
            raise

class ServiceNotifier:
    @staticmethod
    def notify_user_created(user_data: Dict):
        """Notify other services about new user creation"""
        try:
            # Notify User Management Service
            MicroserviceClient.send_request(
                service='user_management',
                endpoint='/api/users/sync',
                method='POST',
                data=user_data
            )
            
            # Notify Notification Service for welcome email
            MicroserviceClient.send_request(
                service='notification',
                endpoint='/api/notifications/welcome',
                method='POST',
                data={'user_id': user_data['id']}
            )
            
        except Exception as e:
            logger.error(f"Error notifying services about user creation: {str(e)}")

    @staticmethod
    def notify_security_event(user_id: int, event_type: str, details: Dict):
        """Notify security-related events to relevant services"""
        try:
            # Notify Fraud Detection Service
            MicroserviceClient.send_request(
                service='fraud_detection',
                endpoint='/api/security-events',
                method='POST',
                data={
                    'user_id': user_id,
                    'event_type': event_type,
                    'details': details
                }
            )
            
            # Notify Notification Service if needed
            if event_type in ['ACCOUNT_LOCKED', 'SUSPICIOUS_ACTIVITY']:
                MicroserviceClient.send_request(
                    service='notification',
                    endpoint='/api/notifications/security-alert',
                    method='POST',
                    data={
                        'user_id': user_id,
                        'alert_type': event_type,
                        'details': details
                    }
                )
                
        except Exception as e:
            logger.error(f"Error notifying security event: {str(e)}")