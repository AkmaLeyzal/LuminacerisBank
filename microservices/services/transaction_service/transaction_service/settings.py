import os
from datetime import timedelta
from pathlib import Path
import sys

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent.parent.parent

sys.path.append(str(ROOT_DIR))

if not os.getenv('DOCKER_CONTAINER'):
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, '.env'))

# Secret key for Django, fetched from environment variables for security
SECRET_KEY = os.getenv('SECRET_KEY_TRANSACTION_SERVICE', 'default_secret_key')

# Service Authentication
SERVICE_AUTH_KEY = os.getenv('SERVICE_AUTH_KEY', 'LuminacerisBank_is_the_best_bank_ever')


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
    'transaction',  # Main app for this service
]

# Middleware configuration including CORS
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Root URL configuration
ROOT_URLCONF = 'transaction_service.urls'

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
WSGI_APPLICATION = 'transaction_service.wsgi.application'

# Database configuration (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'transaction_rds'),
        'USER': os.getenv('DATABASE_USER', 'transaction_admin'),
        'PASSWORD': os.getenv('TRANSACTION_DB_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}

# Transaction Service Settings
TRANSACTION_SETTINGS = {
    'DAILY_LIMIT': float(os.getenv('TRANSACTION_DAILY_LIMIT', '50000')),
    'RATE_LIMIT_PER_MINUTE': int(os.getenv('TRANSACTION_RATE_LIMIT', '10')),
    'MAX_AMOUNT_PER_TRANSACTION': float(os.getenv('MAX_TRANSACTION_AMOUNT', '1000000000')),
    'MIN_AMOUNT_PER_TRANSACTION': float(os.getenv('MIN_TRANSACTION_AMOUNT', '0.01')),
    'FEE_SETTINGS': {
        'BASE_FEE': float(os.getenv('TRANSACTION_BASE_FEE', '1.00')),
        'PERCENTAGE_FEE': float(os.getenv('TRANSACTION_PERCENTAGE_FEE', '0.001'))  # 0.1%
    },
    'CACHE_TIMEOUT': {
        'TRANSACTION_STATUS': 3600,    # 1 hour
        'ACCOUNT_BALANCE': 300,        # 5 minutes
        'RATE_LIMIT': 60,             # 1 minute
        'DAILY_TOTAL': 86400          # 24 hours
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
        "LOCATION": f"redis://redis-14028.c334.asia-southeast2-1.gce.redns.redis-cloud.com:{REDIS_PORT}/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": os.getenv('REDIS_PASSWORD'),
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 20,  # Reduce for small scale
                "timeout": 5
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

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,  # Menggunakan SECRET_KEY yang sudah ada
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
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

REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle'
]

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/day',
    'user': '1000/day',
    'transaction': '10/minute'
}

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

KAFKA_SETTINGS = {
    'BOOTSTRAP_SERVERS': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
    'SECURITY_PROTOCOL': "SASL_SSL",
    'SASL_MECHANISMS': "PLAIN",
    'SASL_USERNAME': os.getenv('CONFLUENT_SASL_USERNAME'),
    'SASL_PASSWORD': os.getenv('CONFLUENT_SASL_PASSWORD'),
    'CLIENT_ID': os.getenv('CONFLUENT_CLIENT_ID'),
    'TOPICS': {
        'TRANSACTION_EVENTS': 'transaction-events',
        'ACCOUNT_EVENTS': 'account-events',
        'NOTIFICATION_EVENTS': 'notification-events'
    }
}

# Internationalization settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Jakarta'
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
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'transaction_service.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'transaction': {  # Add app-specific logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

# Ensure logs directory exists
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# if not DEBUG:
#     SECURE_SSL_REDIRECT = True
#     CSRF_COOKIE_SECURE = True
#     SESSION_COOKIE_SECURE = True
#     SECURE_HSTS_SECONDS = 3600
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     SECURE_HSTS_PRELOAD = True
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True