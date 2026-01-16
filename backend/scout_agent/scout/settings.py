"""
Django settings for scout project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'markets',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'scout.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'scout.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Data directory
DATA_DIR = os.getenv('DATA_DIR', './data')

# Hyperliquid settings
HYPERLIQUID = {
    'API_URL': os.getenv('HYPERLIQUID_API_URL', 'https://api.hyperliquid-testnet.xyz'),
    'WS_URL': os.getenv('HYPERLIQUID_WS_URL', 'wss://api.hyperliquid-testnet.xyz/ws'),
    'RECONNECT_DELAY': int(os.getenv('WS_RECONNECT_DELAY', 5)),
}

# Signal thresholds
SIGNAL_CONFIG = {
    'ZSCORE_THRESHOLD': float(os.getenv('ZSCORE_THRESHOLD', 2.0)),
    'CORRELATION_THRESHOLD': float(os.getenv('CORRELATION_THRESHOLD', 0.7)),
    'MIN_CONFIDENCE': float(os.getenv('MIN_CONFIDENCE', 0.6)),
}

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Rolling window sizes
SIGNAL_WINDOW_SIZE = int(os.getenv('SIGNAL_WINDOW_SIZE', 1000))
LOG_WINDOW_SIZE = int(os.getenv('LOG_WINDOW_SIZE', 100))
PRICE_HISTORY_SIZE = int(os.getenv('PRICE_HISTORY_SIZE', 100))

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
]

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
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
        'level': LOG_LEVEL,
    },
}
