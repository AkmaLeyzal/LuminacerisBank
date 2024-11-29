# authentication/services.py

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import pytz
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import timedelta
from typing import Dict, Tuple, Optional
import secrets
import logging

from .models import User, UserSession, SecurityAuditLog
from .utils.token_utils import TokenManager
from .utils.microservices import ServiceNotifier
from kafka_cloud.producer import KafkaProducer
from kafka_cloud.topics import KafkaTopics
from .utils.ses_utils import SESEmailService, AuthEmailService, EmailTemplateService
from .utils.cache_utils import CacheService, TokenCache, SessionCache, RateLimitCache

logger = logging.getLogger(__name__)
kafka_producer = KafkaProducer()
email_service = AuthEmailService()
cache_service = CacheService()
timezone.activate(pytz.timezone('Asia/Jakarta'))

class RegistrationService:
    @staticmethod
    def register_user(data: Dict) -> Tuple[User, str]:
        """Handle user registration process"""
        try:
            # Create user with pending status
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                full_name=data['full_name'],
                phone_number=data.get('phone_number'),
                # status=User.Status.PENDING,
                # is_active=False
                status=User.Status.ACTIVE,  # Langsung set ACTIVE
                is_active=True,            # Langsung set True
                is_email_verified=True     # Langsung set True
            )

            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            user.email_verification_token = verification_token
            user.save()

            # Cache verification token
            # cache_key = f"email_verification:{verification_token}"
            # cache.set(cache_key, user.id, timeout=3600)  # 1 hour expiry

            # Send verification email menggunakan SES
            # if not email_service.send_verification_email(user, verification_token):
            #     logger.error(f"Failed to send verification email to {user.email}")

            # Notify other services
            user_data = {
                'id': user.user_id,
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name,
                'status': user.status
            }
            # ServiceNotifier.notify_user_created(user_data)

            # Produce Kafka event
            kafka_producer.produce(
                topic=KafkaTopics.USER_EVENTS,
                key=str(user.user_id),
                value={
                    "event_type": "USER_REGISTERED",
                    "user_id": user.user_id,
                    "email": user.email,
                    "timestamp": timezone.now().isoformat()
                }
            )

            return user, None, #verification_token hanya digunakan jika frondend sudah ada

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise

    @staticmethod
    def verify_email(token: str) -> bool:
        """Verify user email with token"""
        cache_key = f"email_verification:{token}"
        user_id = cache.get(cache_key)

        if not user_id:
            raise ValueError("Invalid or expired verification token")

        try:
            user = User.objects.get(id=user_id)
            if user.email_verification_token != token:
                raise ValueError("Invalid verification token")

            user.is_email_verified = True
            user.status = User.Status.ACTIVE
            user.is_active = True
            user.email_verification_token = None
            user.save()

            # Clear verification token from cache
            cache_service.delete(cache_key)

            # Produce Kafka event
            kafka_producer.produce(
                topic=KafkaTopics.USER_EVENTS,
                key=str(user.user_id),
                value={
                    "event_type": "EMAIL_VERIFIED",
                    "user_id": user.user_id,
                    "email": user.email,
                    "timestamp": timezone.now().isoformat()
                }
            )

            return True

        except User.DoesNotExist:
            raise ValueError("User not found")
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            raise

    @staticmethod
    def _send_verification_email(user: User, token: str):
        """Send email verification email"""
        try:
            context = {
                'user': user,
                'verification_url': f"{settings.FRONTEND_URL}/verify-email?token={token}"
            }
            html_message = render_to_string('email/verify_email.html', context)

            send_mail(
                subject="Verify your Luminaceris Bank account",
                message="",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            raise

class AuthenticationService:
    @staticmethod
    def authenticate_user(email: str, password: str, request_data: Dict) -> User:
        """Authenticate user and handle security checks"""
        try:
            ip_address = request_data.get('ip_address', '')
            
            # Check rate limiting using RateLimitCache
            attempts = RateLimitCache.get_attempts(ip_address, 'LOGIN')
            
            if attempts >= settings.SECURITY_CONFIG['LOGIN']['MAX_ATTEMPTS']:
                raise ValueError("Too many login attempts. Please try again later.")

            try:
                user = User.objects.get(email=email.lower())
            except User.DoesNotExist:
                RateLimitCache.increment_attempts(ip_address, 'LOGIN')
                raise ValueError("Invalid credentials")

            if not user.check_password(password):
                AuthenticationService._handle_failed_login(user, ip_address)
                raise ValueError("Invalid credentials")

            # Check user status
            if user.status != User.Status.ACTIVE:
                raise ValueError(f"Account is {user.status}")

            if not user.is_email_verified:
                raise ValueError("Email not verified")

             # Reset failed attempts
            RateLimitCache.reset_attempts(ip_address, 'LOGIN')
            
            # Update user
            user.failed_login_attempts = 0
            user.last_login_ip = ip_address
            user.last_login_date = timezone.now()
            user.last_activity = timezone.now()
            user.save()

            # Check for suspicious activity
            # try:
            #     fraud_check = ServiceNotifier.notify_security_event({
            #         'user_id': user.id,
            #         'ip_address': ip_address,
            #         'user_agent': request_data.get('user_agent'),
            #         'device_id': request_data.get('device_id')
            #     })
                
            #     if fraud_check.get('risk_level') == 'HIGH':
            #         raise ValueError("Login blocked for security reasons")
            # except Exception as e:
            #     logger.error(f"Fraud check error: {str(e)}")

            return user

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise

    @staticmethod
    def create_session(user: User, tokens: Dict, request_data: Dict) -> UserSession:
        """Create new user session"""
        session = UserSession.objects.create(
            user=user,
            access_token_jti=tokens['access_token_id'],
            refresh_token_jti=tokens['refresh_token_id'],
            device_id=request_data.get('device_id'),
            device_name=request_data.get('device_name'),
            device_type=request_data.get('device_type'),
            user_agent=request_data.get('user_agent', ''),
            ip_address=request_data.get('ip_address'),
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Cache session data
        session_data = {
            'user_id': user.user_id,
            'access_token_jti': tokens['access_token_id'],
            'device_id': request_data.get('device_id'),
            'is_active': True
        }
        SessionCache.store_session(
            str(session.session_id),
            session_data,
            expires_in=7*24*60*60
        )

        # Log security audit
        SecurityAuditLog.objects.create(
            user=user,
            event_type='LOGIN',
            ip_address=request_data.get('ip_address'),
            user_agent=request_data.get('user_agent', ''),
            event_details={
                'device_id': request_data.get('device_id'),
                'session_id': str(session.session_id)
            }
        )

        return session

    @staticmethod
    def _handle_failed_attempt(rate_limit_key: str):
        """Handle failed login attempt"""
        cache.incr(rate_limit_key)
        cache.expire(
            rate_limit_key, 
            settings.SECURITY_CONFIG['LOGIN']['MAX_ATTEMPTS']
        )

    @staticmethod
    def _handle_failed_login(user: User, rate_limit_key: str):
        """Handle failed login for existing user"""
        user.failed_login_attempts += 1
        user.last_failed_login = timezone.now()
        user.save()

        AuthenticationService._handle_failed_attempt(rate_limit_key)

        if user.failed_login_attempts >= settings.SECURITY_CONFIG['LOGIN']['MAX_ATTEMPTS']:
            user.status = User.Status.LOCKED
            user.save()

            ServiceNotifier.notify_security_event(
                user_id=user.user_id,
                event_type='ACCOUNT_LOCKED',
                details={'reason': 'Too many failed login attempts'}
            )

class PasswordService:
    @staticmethod
    def initiate_reset(email: str) -> Optional[str]:
        """Initiate password reset process"""
        try:
            user = User.objects.get(email=email.lower())
            
            # Generate OTP
            otp = ''.join(secrets.choice('0123456789') for _ in range(6))
            
            # Cache OTP
            cache_key = f"password_reset_otp:{email.lower()}"
            cache.set(cache_key, otp, timeout=300)  # 5 minutes

            # Send OTP email menggunakan SES
            if not email_service.send_password_reset_email(user, otp):
                logger.error(f"Failed to send password reset email to {email}")
                raise ValueError("Failed to send reset email")
            
            # Log security audit
            SecurityAuditLog.objects.create(
                user=user,
                event_type='PASSWORD_RESET_INITIATED',
                ip_address='system',
                user_agent='system',
                event_details={'email': email}
            )

            return otp

        except User.DoesNotExist:
            # Return None but don't indicate if user exists
            return None
        except Exception as e:
            logger.error(f"Password reset initiation error: {str(e)}")
            raise

    @staticmethod
    def verify_otp(email: str, otp: str) -> bool:
        """Verify password reset OTP"""
        cache_key = cache_service.generate_key('PASSWORD_RESET', email.lower())
        stored_otp = cache_service.get(cache_key)

        if not stored_otp or stored_otp != otp:
            return False

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        token_key = f"password_reset_token:{reset_token}"
        cache_service.set(token_key, email.lower(), timeout=900)  # 15 minutes

        # Clear OTP
        cache_service.delete(cache_key)

        return True

    @staticmethod
    def reset_password(token: str, new_password: str) -> bool:
        """Reset user password"""
        try:
            token_key = cache_service.generate_key('PASSWORD_RESET_TOKEN', token)
            email = cache_service.get(token_key)

            if not email:
                raise ValueError("Invalid or expired reset token")

            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.password_changed_at = timezone.now()
            user.save()

            # Invalidate all user sessions
            UserSession.objects.filter(user=user).update(is_active=False)

            # Clear all related cache
            cache_service.delete(token_key)
            SessionCache.invalidate_session(str(user.user_id))

            # Log security audit
            SecurityAuditLog.objects.create(
                user=user,
                event_type='PASSWORD_RESET_COMPLETED',
                ip_address='system',
                user_agent='system',
                event_details={'email': email}
            )

            # Produce Kafka event
            kafka_producer.produce(
                topic=KafkaTopics.SECURITY_EVENTS,
                key=str(user.user_id),
                value={
                    "event_type": "PASSWORD_RESET",
                    "user_id": user.user_id,
                    "timestamp": timezone.now().isoformat()
                }
            )

            return True

        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            raise

    @staticmethod
    def _send_reset_email(user: User, otp: str):
        """Send password reset email with OTP"""
        try:
            context = {
                'user': user,
                'otp': otp,
                'valid_minutes': 5
            }
            html_message = render_to_string('email/password_reset.html', context)

            send_mail(
                subject="Reset Your Luminaceris Bank Password",
                message="",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            raise

class SecurityService:
    @staticmethod
    def handle_suspicious_login(user: User, details: Dict):
        """Handle suspicious login detection"""
        from .events.handlers import SecurityEventHandler
        SecurityEventHandler.handle_suspicious_login(user, details)

    @staticmethod
    def handle_failed_attempts(user: User, details: Dict):
        """Handle multiple failed login attempts"""
        from .events.handlers import SecurityEventHandler
        SecurityEventHandler.handle_failed_attempts(user, details)

    @staticmethod
    def handle_fraud_detection(user: User, details: Dict):
        """Handle fraud detection alert"""
        try:
            # Update user status
            user.status = User.Status.BLOCKED
            user.is_blocked = True
            user.blocked_at = timezone.now()
            user.block_reason = details.get('reason', 'Fraud detection alert')
            user.blocked_by = 'fraud_detection'
            user.save()

            # Invalidate all sessions
            UserSession.objects.filter(user=user).update(is_active=False)

            # Clear user's cache
            cache_service.delete(f"user_permissions:{user.user_id}")

            # Log security audit
            SecurityAuditLog.objects.create(
                user=user,
                event_type='FRAUD_DETECTED',
                ip_address=details.get('ip_address', 'system'),
                user_agent=details.get('user_agent', 'system'),
                event_details=details
            )

            # Send alert email
            email_service.send_account_blocked_email(
                user=user,
                reason="Suspected fraudulent activity"
            )

        except Exception as e:
            logger.error(f"Error handling fraud detection: {str(e)}")
            raise