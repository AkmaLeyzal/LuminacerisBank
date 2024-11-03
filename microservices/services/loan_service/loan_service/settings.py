import os
from datetime import timedelta
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent.parent.parent

if not os.getenv('DOCKER_CONTAINER'):
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, '.env'))

# Secret key for Django, fetched from environment variables for security
SECRET_KEY = os.getenv('SECRET_KEY_LOAN_SERVICE', 'default_secret_key')

# Debug mode
DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't']
# DEBUG = 'True'

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
    'loan',  # Main app for this service
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
ROOT_URLCONF = 'loan_service.urls'

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
WSGI_APPLICATION = 'loan_service.wsgi.application'

# Database configuration (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'loan_rds'),
        'USER': os.getenv('DATABASE_USER', 'loan_admin'),
        'PASSWORD': os.getenv('LOAN_DB_PASSWORD'),
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

# Add to settings.py:
LOAN_SETTINGS = {
    'CACHE_TIMEOUT': {
        'LOAN_STATUS': 3600,      # 1 hour
        'PAYMENT_STATUS': 3600,   # 1 hour
        'SCHEDULE': 3600,         # 1 hour
        'CALCULATIONS': 86400,    # 24 hours
    },
    'DOCUMENT_TYPES': {
        'REQUIRED': ['APPLICATION', 'IDENTITY', 'INCOME'],
        'OPTIONAL': ['COLLATERAL', 'PAYMENT'],
    },
    'LATE_PAYMENT': {
        'GRACE_PERIOD_DAYS': 3,
        'LATE_FEE_PERCENTAGE': float('0.01'),  # 1% late fee
    }
}

REDIS_PORT = 14028

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
    "http://localhost/login_page",
    "http://localhost/home_page",
    "http://localhost/cardManagement_page",
    "http://localhost/fraudAlert_page",
    "http://localhost/history_page",
    "http://localhost/loan_page",
    "http://localhost/notificationCenter_page",
    "http://localhost/paymentService_page",
    "http://localhost/profileSetting_page",
    "http://localhost/support_page",
    "http://localhost/transfer_page",
]

# Additional CORS settings
# CORS_ALLOW_CREDENTIALS = True

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
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# if not DEBUG:
#     SECURE_SSL_REDIRECT = True
#     CSRF_COOKIE_SECURE = True
#     SESSION_COOKIE_SECURE = True
#     SECURE_HSTS_SECONDS = 3600
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     SECURE_HSTS_PRELOAD = True
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True