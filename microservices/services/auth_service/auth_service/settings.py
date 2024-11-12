import os
from datetime import timedelta, datetime
from pathlib import Path
import sys
import json

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent.parent.parent

sys.path.append(str(ROOT_DIR))

if not os.getenv('DOCKER_CONTAINER'):
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, '.env'))

# Secret key for Django, fetched from environment variables for security
SECRET_KEY = os.getenv('SECRET_KEY_AUTH_SERVICE', 'default_secret_key')

# Debug mode
# DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't']
DEBUG = 'True'

# Allowed hosts
ALLOWED_HOSTS = ['*']

# Installed applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',  # For handling CORS
    'rest_framework',  # Django Rest Framework
    'rest_framework_simplejwt.token_blacklist',  # Simple JWT Token Blacklist
    'authentication',  # Main app for this service
]

# Middleware configuration including CORS
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'authentication.utils.formaters.JsonFormatter',
    'authentication.middleware.CORSMiddleware',
    'authentication.middleware.JWTAuthenticationMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Root URL configuration
ROOT_URLCONF = 'auth_service.urls'

# Templates configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Add your template directories here if any
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # Required by Django Allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = 'auth_service.wsgi.application'

AUTH_USER_MODEL = 'authentication.User'

# Database configuration (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'auth_rds'),
        'USER': os.getenv('DATABASE_USER', 'auth_admin'),
        'PASSWORD': os.getenv('AUTH_DB_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = 14028
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": REDIS_PASSWORD,
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 20,  # Reduce for small scale
            },
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
        },
        "KEY_PREFIX": "auth"  # Prefix untuk menghindari konflik
    }
}

# Cache time settings
CACHE_TTL = 60 * 15  # 15 minutes for general cache
CACHE_TTL_SHORT = 60 * 5  # 5 minutes for frequent updates
CACHE_TTL_LONG = 60 * 60 * 24  # 24 hours for stable data

# Cache key patterns
CACHE_KEYS = {
    'TOKEN': 'token:{}',
    'USER_SESSION': 'session:{}',
    'RATE_LIMIT': 'rate:{}:{}',
    'BLACKLIST': 'blacklist:{}',
    'EMAIL_VERIFICATION': 'email_verification:{}',
    'PASSWORD_RESET': 'password_reset_otp:{}'
}

# Session Configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 86400  # 24 hours

# Memory optimization settings for Redis
REDIS_MAX_MEMORY_POLICY = {
    'POLICY': 'allkeys-lru',  # Least Recently Used eviction
    'SAMPLES': 5,
    'MAX_MEMORY': '25mb'  # Keep some buffer from 30mb
}

# Rate limiting settings
RATE_LIMIT = {
    'LOGIN': {
        'ATTEMPTS': 6,
        'WINDOW': 300  # 5 minutes
    },
    'API': {
        'ATTEMPTS': 100,
        'WINDOW': 60  # 1 minute
    }
}

JWT_SECRET_KEY = os.getenv('SECRET_KEY_AUTH_SERVICE')
JWT_REFRESH_SECRET_KEY = os.getenv('SECRET_KEY_AUTH_SERVICE')

# Simple JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': JWT_SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

JWT_AUTH = {
    'JWT_SECRET_KEY': JWT_SECRET_KEY,
    'JWT_REFRESH_SECRET_KEY': JWT_REFRESH_SECRET_KEY,
    'JWT_ALGORITHM': 'HS256',
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=30),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
    'JWT_ALLOW_REFRESH': True,
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    'JWT_AUTH_COOKIE': 'jwt-auth',
    'JWT_AUTH_COOKIE_SECURE': not DEBUG,
    'JWT_AUTH_COOKIE_SAMESITE': 'Lax' if DEBUG else 'None',
    'JWT_AUTH_COOKIE_DOMAIN': os.getenv('COOKIE_DOMAIN', None),
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'authentication.utils.jwt.generate_jwt_payload'
}

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Microservices Communication Settings
MICROSERVICES = {
    'user_management': {
        'base_url': f"http://{os.getenv('USER_MANAGEMENT_SERVICE_HOST', 'user_management_service')}:8002",
        'timeout': 5,
    },
    'notification': {
        'base_url': f"http://{os.getenv('NOTIFICATION_SERVICE_HOST', 'notification_service')}:8008",
        'timeout': 5,
    },
    'fraud_detection': {
        'base_url': f"http://{os.getenv('FRAUD_DETECTION_SERVICE_HOST', 'fraud_detection_service')}:8010",
        'timeout': 5,
    }
}

# AWS SES Configuration
AWS_SES_ACCESS_KEY_ID = os.getenv('AWS_SES_ACCESS_KEY_ID')
AWS_SES_SECRET_ACCESS_KEY = os.getenv('AWS_SES_SECRET_ACCESS_KEY')
AWS_SES_REGION = os.getenv('AWS_SES_REGION')
AWS_SES_CONFIGURATION_SET = os.getenv('AWS_SES_CONFIGURATION_SET')

# Email Settings
DEFAULT_FROM_EMAIL = 'luminacerisbank@gmail.com'  # Verified domain di SES
SERVER_EMAIL = 'luminacerisbank@gmail.com'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = f'email-smtp.{AWS_SES_REGION}.amazonaws.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = AWS_SES_ACCESS_KEY_ID
EMAIL_HOST_PASSWORD = AWS_SES_SECRET_ACCESS_KEY

# Template Context
EMAIL_TEMPLATE_CONTEXT = {
    'company_name': 'Luminaceris Bank',
    'support_email': 'luminacerisbank@gmail.com',
    'website_url': os.getenv('FRONTEND_URL', 'http://localhost:3000'),
    'company_address': 'Jl. Ketintang Baru XII No 34, Ketintang, Kec. Gayungan, Surabaya, Jawa Timur 60231',
    'contact_phone': '+62 856789012',
    'social_media': {
        'facebook': 'https://facebook.com/luminacerisbank',
        'twitter': 'https://twitter.com/luminacerisbank',
        'instagram': 'https://instagram.com/luminacerisbank'
    }
}
# Django Rest Framework settings 
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_PAGINATION_CLASS': 
        'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}

REST_FRAMEWORK.update({
    'EXCEPTION_HANDLER': 'authentication.utils.exception_handlers.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/minute',
        'user': '1000/minute'
    }
})

# Template Configuration untuk email templates
TEMPLATES[0]['DIRS'] = [
    os.path.join(BASE_DIR, 'authentication', 'templates')
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:80",     # Nginx
    "http://localhost:8001",   # Auth Service
    "http://localhost:8002",   # User Management Service
    "http://localhost:8003",   # Account Service
    "http://localhost:8004",   # Transaction Service
    "http://localhost:8005",   # Payment Service
    "http://localhost:8006",   # Card Management Service
    "http://localhost:8007",   # Loan Service
    "http://localhost:8008",   # Notification Service
    "http://localhost:8009",   # Audit Service
    "http://localhost:8010",   # Fraud Detection Service
    "http://localhost:8011",   # Support Service
    # Frontend origins
    "http://localhost:3000",   # React development
    # "http://localhost/login_page",
    # "http://localhost/home_page",
    # "http://localhost/cardManagement_page",
    # "http://localhost/fraudAlert_page",
    # "http://localhost/history_page",
    # "http://localhost/loan_page",
    # "http://localhost/notificationCenter_page",
    # "http://localhost/paymentService_page",
    # "http://localhost/profileSetting_page",
    # "http://localhost/support_page",
    # "http://localhost/transfer_page",
]

# Additional CORS settings
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-api-key',
    'cache-control',
    'pragma'
]

CORS_EXPOSE_HEADERS = [
    'Content-Type',
    'Authorization',
    'X-CSRFToken',
]

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')

# Internationalization settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files configuration
STATIC_URL = '/static/'

# Tambahkan pengaturan STATIC_ROOT
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'authentication.utils.formatters.JsonFormatter',
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'authentication.utils.handlers.SafeFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'auth_service.log'),
            'formatter': 'json',
            'maxBytes': 1024 * 1024 * 100,  # 100 MB
            'backupCount': 5,  # Keep 5 backup files
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'authentication': {
            'handlers': ['file', 'console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'django': {
            'handlers': ['file', 'console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
    }
}

ENV_NAME = os.getenv('ENV_NAME', 'development')

LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# if not DEBUG:
#     SECURE_SSL_REDIRECT = True
#     CSRF_COOKIE_SECURE = True
#     SESSION_COOKIE_SECURE = True
#     SECURE_HSTS_SECONDS = 3600
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     SECURE_HSTS_PRELOAD = True
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True