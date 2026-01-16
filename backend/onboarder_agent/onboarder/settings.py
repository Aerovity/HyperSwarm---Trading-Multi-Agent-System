"""
Django settings for onboarder project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'bridge',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'onboarder.urls'

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

WSGI_APPLICATION = 'onboarder.wsgi.application'

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
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Data directory
DATA_DIR = os.getenv('DATA_DIR', './data')

# LI.FI Configuration
LIFI = {
    'API_URL': os.getenv('LIFI_API_URL', 'https://li.quest/v1'),
    'API_KEY': os.getenv('LIFI_API_KEY', ''),
    'INTEGRATOR': os.getenv('LIFI_INTEGRATOR', 'hyperswarm-hackathon'),
}

# Hyperliquid Configuration
HYPERLIQUID = {
    'API_URL': os.getenv('HYPERLIQUID_API_URL', 'https://api.hyperliquid-testnet.xyz'),
}

# Service Configuration
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 1))

# Supported Chains
SOURCE_CHAINS = os.getenv('SOURCE_CHAINS', '137,42161,8453,10').split(',')
DESTINATION_CHAIN = os.getenv('DESTINATION_CHAIN', '998')

# Cache Settings
QUOTE_CACHE_TTL = int(os.getenv('QUOTE_CACHE_TTL', 30))
QUOTE_WINDOW_SIZE = int(os.getenv('QUOTE_WINDOW_SIZE', 100))
TRANSACTION_WINDOW_SIZE = int(os.getenv('TRANSACTION_WINDOW_SIZE', 500))
LOG_WINDOW_SIZE = int(os.getenv('LOG_WINDOW_SIZE', 100))

# Rate Limiting
RATE_LIMIT_CALLS = int(os.getenv('RATE_LIMIT_CALLS', 10))
RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', 1))

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
