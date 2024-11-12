# LuminacerisBank/kafka/topics.py
from typing import List
class KafkaTopics:
    """Kafka topics configuration"""
    
    # User-related events
    USER_EVENTS = 'user-events'
    USER_CREATED = 'user-created'
    USER_UPDATED = 'user-updated'
    
    # Security events
    SECURITY_EVENTS = 'security-events'
    LOGIN_ATTEMPTS = 'login-attempts'
    SUSPICIOUS_ACTIVITIES = 'suspicious-activities'
    
    # System events
    AUDIT_LOGS = 'audit-logs'
    SYSTEM_NOTIFICATIONS = 'system-notifications'
    
    # Service-specific events
    AUTH_EVENTS = 'auth-events'
    ACCOUNT_EVENTS = 'account-events'
    TRANSACTION_EVENTS = 'transaction-events'
    
    @classmethod
    def get_all_topics(cls) -> List[str]:
        """Get list of all available topics"""
        return [
            value for name, value in vars(cls).items()
            if not name.startswith('_') and isinstance(value, str)
        ]