# authentication/utils/ses_utils.py

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SESEmailService:
    def __init__(self):
        """Initialize AWS SES client"""
        self.client = boto3.client(
            'ses',
            aws_access_key_id=settings.AWS_SES_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SES_SECRET_ACCESS_KEY,
            region_name=settings.AWS_SES_REGION
        )
        self.source_email = settings.DEFAULT_FROM_EMAIL
        self.configuration_set = settings.AWS_SES_CONFIGURATION_SET

    def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        reply_to: Optional[List[str]] = None,
        tags: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """
        Send email using AWS SES
        
        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            reply_to: List of reply-to addresses (optional)
            tags: List of message tags for tracking (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            message = {
                'Subject': {'Data': subject},
                'Body': {
                    'Html': {'Data': html_content}
                }
            }

            if text_content:
                message['Body']['Text'] = {'Data': text_content}

            email_params = {
                'Source': self.source_email,
                'Destination': {
                    'ToAddresses': to_addresses
                },
                'Message': message,
            }

            # Add ConfigurationSetName if specified
            if self.configuration_set:
                email_params['ConfigurationSetName'] = self.configuration_set

            # Add ReplyToAddresses if specified
            if reply_to:
                email_params['ReplyToAddresses'] = reply_to

            # Add message tags if specified
            if tags:
                email_params['Tags'] = tags

            response = self.client.send_email(**email_params)
            
            logger.info(f"Email sent successfully. MessageId: {response['MessageId']}")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to send email: {error_code} - {error_message}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return False

class EmailTemplateService:
    def __init__(self):
        self.ses_service = SESEmailService()

    def send_templated_email(
        self,
        template_name: str,
        context: dict,
        to_email: str,
        subject: str,
        tags: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """Send templated email using AWS SES"""
        try:
            # Add global template context
            context.update(settings.EMAIL_TEMPLATE_CONTEXT)

            # Render template
            html_content = render_to_string(
                f'email/{template_name}.html',
                context
            )
            text_content = strip_tags(html_content)

            # Add default tags
            default_tags = [
                {'Name': 'template', 'Value': template_name},
                {'Name': 'environment', 'Value': settings.ENV_NAME}
            ]
            if tags:
                tags.extend(default_tags)
            else:
                tags = default_tags

            return self.ses_service.send_email(
                to_addresses=[to_email],
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                tags=tags
            )

        except Exception as e:
            logger.error(f"Failed to send templated email: {str(e)}")
            return False

class AuthEmailService:
    def __init__(self):
        self.template_service = EmailTemplateService()

    def send_verification_email(self, user, verification_token: str) -> bool:
        """Send email verification email"""
        try:
            context = {
                'user': user,
                'verification_url': f"{settings.FRONTEND_URL}/verify-email?token={verification_token}",
                'verification_token': verification_token,
                'expiry_hours': 1
            }

            tags = [
                {'Name': 'email_type', 'Value': 'verification'},
                {'Name': 'user_id', 'Value': str(user.id)}
            ]

            return self.template_service.send_templated_email(
                template_name='verify_email',
                context=context,
                to_email=user.email,
                subject='Verify your Luminaceris Bank account',
                tags=tags
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return False

    def send_password_reset_email(self, user, otp: str) -> bool:
        """Send password reset OTP email"""
        try:
            context = {
                'user': user,
                'otp': otp,
                'expiry_minutes': 5
            }

            tags = [
                {'Name': 'email_type', 'Value': 'password_reset'},
                {'Name': 'user_id', 'Value': str(user.id)}
            ]

            return self.template_service.send_templated_email(
                template_name='password_reset',
                context=context,
                to_email=user.email,
                subject='Reset your Luminaceris Bank password',
                tags=tags
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return False
        
        