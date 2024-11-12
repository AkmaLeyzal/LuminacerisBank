# authentication/events/handlers.py
from ..models import User, SecurityAuditLog
from ..utils.ses_utils import AuthEmailService
from typing import Dict
import logging

logger = logging.getLogger(__name__)
email_service = AuthEmailService()

class SecurityEventHandler:
    @staticmethod
    def handle_suspicious_login(user: User, data: Dict):
        """Handle suspicious login event"""
        try:
            # Log security audit
            SecurityAuditLog.objects.create(
                user=user,
                event_type='SUSPICIOUS_LOGIN',
                ip_address=data.get('ip_address', ''),
                user_agent=data.get('user_agent', ''),
                event_details=data
            )

            # Send alert email
            email_service.send_security_alert_email(
                user=user,
                alert_type='Suspicious Login Detected',
                details=data
            )

        except Exception as e:
            logger.error(f"Error handling suspicious login: {str(e)}")

    @staticmethod
    def handle_failed_attempts(user: User, data: Dict):
        """Handle multiple failed login attempts"""
        try:
            # Update user status
            user.status = User.Status.LOCKED
            user.save()

            # Log security audit
            SecurityAuditLog.objects.create(
                user=user,
                event_type='ACCOUNT_LOCKED',
                ip_address=data.get('ip_address', ''),
                user_agent=data.get('user_agent', ''),
                event_details={
                    'reason': 'Multiple failed login attempts',
                    **data
                }
            )

            # Send alert email
            email_service.send_account_locked_email(
                user=user,
                reason="Multiple failed login attempts detected"
            )

        except Exception as e:
            logger.error(f"Error handling failed attempts: {str(e)}")
