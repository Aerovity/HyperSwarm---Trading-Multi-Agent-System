"""
Django settings for Guardian Agent project.
Risk management service with LLM-powered trade approval.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-guardian-dev-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'risk',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'guardian.urls'

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

WSGI_APPLICATION = 'guardian.wsgi.application'

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

# Data directory for JSON persistence
DATA_DIR = os.getenv('DATA_DIR', str(BASE_DIR / 'data'))

# Hyperliquid Configuration
HYPERLIQUID = {
    'API_URL': os.getenv('HYPERLIQUID_API_URL', 'https://api.hyperliquid-testnet.xyz'),
}

# Anthropic/Claude Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')

# Demo mode (skip real API calls for testing)
DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'

# Redis Configuration - DB 2 for Guardian (Scout=0, Onboarder=1)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 2))

# Cache Settings
PORTFOLIO_CACHE_TTL = int(os.getenv('PORTFOLIO_CACHE_TTL', 60))
RISK_METRICS_CACHE_TTL = int(os.getenv('RISK_METRICS_CACHE_TTL', 30))
APPROVAL_WINDOW_SIZE = int(os.getenv('APPROVAL_WINDOW_SIZE', 100))
ALERT_WINDOW_SIZE = int(os.getenv('ALERT_WINDOW_SIZE', 200))
LOG_WINDOW_SIZE = int(os.getenv('LOG_WINDOW_SIZE', 100))

# Risk Limits Configuration
RISK_LIMITS = {
    'MAX_POSITIONS': int(os.getenv('MAX_POSITIONS', 3)),
    'MAX_LEVERAGE': float(os.getenv('MAX_LEVERAGE', 3.0)),
    'MAX_POSITION_PCT': float(os.getenv('MAX_POSITION_PCT', 0.30)),
    'MIN_LIQUIDATION_DISTANCE': float(os.getenv('MIN_LIQUIDATION_DISTANCE', 0.20)),
    'MIN_SIGNAL_CONFIDENCE': float(os.getenv('MIN_SIGNAL_CONFIDENCE', 0.7)),
}

# RL Policy Configuration (DEPRECATED - use Reflexion instead)
USE_RL_POLICY = os.getenv('USE_RL_POLICY', 'false').lower() == 'true'
RL_MODEL_PATH = os.getenv('RL_MODEL_PATH', str(BASE_DIR / 'data' / 'models' / 'guardian_ppo_latest'))
RL_DETERMINISTIC = os.getenv('RL_DETERMINISTIC', 'true').lower() == 'true'
RL_FALLBACK_TO_RULES = os.getenv('RL_FALLBACK_TO_RULES', 'true').lower() == 'true'

# Reflexion Configuration (text-based learning from past decisions)
USE_REFLEXION = os.getenv('USE_REFLEXION', 'true').lower() == 'true'
REFLEXION_REDIS_DB = int(os.getenv('REFLEXION_REDIS_DB', 3))

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
]

# REST Framework
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
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'risk': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}
