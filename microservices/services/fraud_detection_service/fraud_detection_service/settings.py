import os
from datetime import timedelta
from pathlib import Path
import mongoengine  # DIUBAH: Tambahkan ini untuk MongoEngine

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent.parent.parent

if not os.getenv('DOCKER_CONTAINER'):
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, '.env'))

# Secret key for Django, fetched from environment variables for security
SECRET_KEY = os.getenv('SECRET_KEY_FRAUD_SERVICE', 'default_secret_key')

# Debug mode
DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't']

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
    'rest_framework_mongoengine',  # DIUBAH: Tambahkan ini untuk integrasi DRF dengan MongoEngine
    'fraud',  # Main app for this service
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
ROOT_URLCONF = 'fraud_detection_service.urls'

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
WSGI_APPLICATION = 'fraud_detection_service.wsgi.application'

# Menghapus konfigurasi DATABASES karena MongoEngine digunakan
# DATABASES = {
#     'default': {
#         'ENGINE': 'djongo',
#         'NAME': os.getenv('DATABASE_NAME', 'fraud_db'),
#         'CLIENT': {
#             'host': f"mongodb+srv://{os.getenv('MONGODB_USERNAME')}:{os.getenv('MONGODB_PASSWORD')}@akmaleyzaldatabases.lfu1fxc.mongodb.net/",
#             'authMechanism': 'SCRAM-SHA-1',
#         },
#     }
# }

# DIUBAH: Konfigurasi MongoEngine
MONGODB_SETTINGS = {
    'db': 'fraud_db',
    'username': os.getenv('MONGODB_USERNAME'),
    'password': os.getenv('MONGODB_PASSWORD'),
    'host': f"mongodb+srv://{os.getenv('MONGODB_USERNAME')}:{os.getenv('MONGODB_PASSWORD')}@akmaleyzaldatabases.lfu1fxc.mongodb.net/",
    'authentication_source': 'admin',  # Sesuaikan jika diperlukan
}

# DIUBAH: Inisialisasi koneksi MongoEngine
mongoengine.connect(
    db=MONGODB_SETTINGS['db'],
    username=MONGODB_SETTINGS['username'],
    password=MONGODB_SETTINGS['password'],
    host=MONGODB_SETTINGS['host'],
    authentication_source=MONGODB_SETTINGS.get('authentication_source', 'admin'),
)

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
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

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS')
KAFKA_SECURITY_PROTOCOL = "SASL_SSL"
KAFKA_SASL_MECHANISMS = "PLAIN"
KAFKA_SASL_USERNAME = os.getenv('CONFLUENT_SASL_USERNAME')
KAFKA_SASL_PASSWORD = os.getenv('CONFLUENT_SASL_PASSWORD')

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

# Hapus konfigurasi LOGGING yang lama dan ganti dengan ini
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'DEBUG',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'auth_service.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'INFO',
        }
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'authentication': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

# Service URLs
AUTH_SERVICE_URL = 'http://localhost:8001'
USER_MANAGEMENT_SERVICE_URL = 'http://localhost:8002'
ACCOUNT_SERVICE_URL = 'http://localhost:8003'
TRANSACTION_SERVICE_URL = 'http://localhost:8004'
PAYMENT_SERVICE_URL = 'http://localhost:8005'
CARD_MANAGEMENT_SERVICE_URL = 'http://localhost:8006'
LOAN_SERVICE_URL = 'http://localhost:8007'
NOTIFICATION_SERVICE_URL = 'http://localhost:8008'
AUDIT_SERVICE_URL = 'http://localhost:8009'
FRAUD_DETECTION_SERVICE_URL = 'http://localhost:8010'
SUPPORT_SERVICE_URL = 'http://localhost:8011'

# Ensure logs directory exists
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR, exist_ok=True)

ENV_NAME = os.getenv('ENV_NAME', 'development')


# if not DEBUG:
#     SECURE_SSL_REDIRECT = True
#     CSRF_COOKIE_SECURE = True
#     SESSION_COOKIE_SECURE = True
#     SECURE_HSTS_SECONDS = 3600
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     SECURE_HSTS_PRELOAD = True
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
