import os
from datetime import timedelta
from pathlib import Path
import mongoengine

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Secret key for Django, fetched from environment variables for security
SECRET_KEY = os.getenv('SECRET_KEY_AUDIT_SERVICE', 'default_secret_key')

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
    # 'rest_framewrok_mongoengine',  # Using MongoDB with Django
    # 'audit',  # Main app for this service
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
ROOT_URLCONF = 'audit_service.urls'

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
WSGI_APPLICATION = 'audit_service.wsgi.application'

# Database configuration (MongoDB)
# DATABASES = {
#     'default': {
#         'ENGINE': 'djongo',
#         'NAME': os.getenv('DATABASE_NAME', 'audit_db'),
#         'CLIENT': {
#             'host': f"mongodb+srv://{os.getenv('MONGODB_USERNAME')}:{os.getenv('MONGODB_PASSWORD')}@akmaleyzaldatabases.lfu1fxc.mongodb.net/",
#             'authMechanism': 'SCRAM-SHA-1',
#         },
#     }
# }

MONGODB_SETTINGS = {
    'db': 'audit_db',
    'username': os.getenv('MONGODB_USERNAME'),
    'password': os.getenv('MONGODB_PASSWORD'),
    'host': f'mongodb+srv://{os.getenv('MONGODB_USERNAME')}:{os.getenv('MONGODB_PASSWORD')}@akmaleyzaldatabases.lfu1fxc.mongodb.net/',
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

# Django Rest Framework settings with Simple JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# Simple JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# CORS settings to allow specified origins
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://your-production-frontend.com',
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