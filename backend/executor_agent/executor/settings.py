"""
Django settings for executor project.
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

# Demo mode - use mocked API responses
DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'trading',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'executor.urls'

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

WSGI_APPLICATION = 'executor.wsgi.application'


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

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 3))

# Hyperliquid configuration
HYPERLIQUID = {
    'API_URL': os.getenv('HYPERLIQUID_API_URL', 'https://api.hyperliquid-testnet.xyz'),
    'WALLET_KEY': os.getenv('HYPERLIQUID_WALLET_KEY', ''),
    'WALLET_ADDRESS': os.getenv('HYPERLIQUID_WALLET_ADDRESS', ''),
}

# Pear Protocol configuration
PEAR = {
    'API_URL': os.getenv('PEAR_API_URL', 'https://hl-v2-testnet.pearprotocol.io'),
    'API_KEY': os.getenv('PEAR_API_KEY', ''),
    'BUILDER_CODE': os.getenv('PEAR_BUILDER_CODE', ''),
}

# Risk control settings
RISK_CONTROLS = {
    'MAX_CONCURRENT_POSITIONS': int(os.getenv('MAX_CONCURRENT_POSITIONS', 3)),
    'MAX_POSITION_ALLOCATION': float(os.getenv('MAX_POSITION_ALLOCATION', 0.30)),
    'MAX_LEVERAGE': float(os.getenv('MAX_LEVERAGE', 3.0)),
    'MIN_PORTFOLIO_VALUE': float(os.getenv('MIN_PORTFOLIO_VALUE', 100)),
}

# TWAP settings
TWAP = {
    'THRESHOLD': float(os.getenv('TWAP_THRESHOLD', 1000)),
    'CHUNKS': int(os.getenv('TWAP_CHUNKS', 5)),
    'INTERVAL': int(os.getenv('TWAP_INTERVAL', 180)),
}

# Position management settings
POSITION = {
    'TP_SIGMA': float(os.getenv('TP_SIGMA', 0.5)),
    'SL_SIGMA': float(os.getenv('SL_SIGMA', 3.0)),
    'MONITOR_INTERVAL': int(os.getenv('MONITOR_INTERVAL', 10)),
}

# Rolling window sizes
POSITION_WINDOW_SIZE = int(os.getenv('POSITION_WINDOW_SIZE', 500))
TRADE_WINDOW_SIZE = int(os.getenv('TRADE_WINDOW_SIZE', 1000))
LOG_WINDOW_SIZE = int(os.getenv('LOG_WINDOW_SIZE', 100))

# Time window settings for spread calculations
TIME_WINDOWS = {
    '1min': {
        'periods': 12,  # 12 periods * 5 seconds = 60 seconds
        'display': '1 minute',
        'duration_seconds': 60
    },
    '5min': {
        'periods': 60,  # 60 periods * 5 seconds = 5 minutes
        'display': '5 minutes',
        'duration_seconds': 300
    },
    '15min': {
        'periods': 180,  # 180 periods * 5 seconds = 15 minutes
        'display': '15 minutes',
        'duration_seconds': 900
    }
}

# Demo settings for hackathon
DEMO_SPREAD_MULTIPLIER = float(os.getenv('DEMO_SPREAD_MULTIPLIER', 7.0))
SPREAD_MIN = float(os.getenv('SPREAD_MIN', 0.001))  # 0.1%
SPREAD_MAX = float(os.getenv('SPREAD_MAX', 0.05))   # 5%

# Other agent URLs
SCOUT_API_URL = os.getenv('SCOUT_API_URL', 'http://localhost:8001')
GUARDIAN_API_URL = os.getenv('GUARDIAN_API_URL', 'http://localhost:8003')

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
