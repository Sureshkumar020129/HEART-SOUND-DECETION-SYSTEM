"""
Django settings for AI-Powered Heart Sound Disease Detection System.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ===========================================================
# SECURITY
# ===========================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production-use-env-var')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    ''
).split(',')

# ===========================================================
# APPLICATIONS
# ===========================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Third-party
    'rest_framework',
    # Project apps
    'core',
    'accounts',
    'dashboard',
    'heart_analysis',
    'assessments',
    'chatbot',
    'reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ===========================================================
# DATABASE
# ===========================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ===========================================================
# AUTHENTICATION
# ===========================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

AUTH_USER_MODEL = 'auth.User'

# ===========================================================
# INTERNATIONALIZATION
# ===========================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ===========================================================
# STATIC AND MEDIA FILES
# ===========================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / os.getenv('MEDIA_ROOT', 'media')

# ===========================================================
# FILE UPLOAD SETTINGS
# ===========================================================
MAX_AUDIO_UPLOAD_MB = int(os.getenv('MAX_AUDIO_UPLOAD_MB', 50))
MAX_UPLOAD_SIZE = MAX_AUDIO_UPLOAD_MB * 1024 * 1024  # bytes
ALLOWED_AUDIO_EXTENSIONS = ['.wav', '.flac', '.mp3', '.ogg', '.aiff']
ALLOWED_AUDIO_CONTENT_TYPES = [
    'audio/wav', 'audio/x-wav', 'audio/flac', 'audio/x-flac',
    'audio/mpeg', 'audio/mp3', 'audio/ogg', 'audio/aiff',
    'audio/x-aiff',
]

# ===========================================================
# ML MODEL SETTINGS
# ===========================================================
ML_MODEL_PATH = BASE_DIR / os.getenv('ML_MODEL_PATH', 'ml_models/heart_sound_classifier.pkl')
ML_SCALER_PATH = BASE_DIR / os.getenv('ML_SCALER_PATH', 'ml_models/scaler.pkl')
ML_MODEL_VERSION = os.getenv('ML_MODEL_VERSION', '1.0.0')
ML_SAMPLE_RATE = 22050
ML_AUDIO_DURATION = 5  # seconds
ML_N_MFCC = 40
ML_HOP_LENGTH = 512
ML_N_FFT = 2048

# ===========================================================
# AI CHATBOT SETTINGS
# ===========================================================
AI_PROVIDER = os.getenv('AI_PROVIDER', '')  # 'openai', 'gemini', 'anthropic', or ''
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
CHATBOT_MAX_HISTORY = 20  # messages per session
CHATBOT_SYSTEM_PROMPT = (
    "You are HeartCare AI Assistant, a helpful and empathetic healthcare education chatbot "
    "for the AI-Powered Heart Sound Disease Detection System. "
    "You provide general educational information about heart sounds, heart health, and how to use this application. "
    "You are NOT a medical professional and cannot diagnose diseases. "
    "Always remind users to consult a qualified healthcare provider for medical advice. "
    "If a user describes symptoms of a medical emergency (severe chest pain, difficulty breathing, fainting), "
    "immediately instruct them to call emergency services (911 in the US, 999 in UK, 112 in EU) and stop the chat."
)

# ===========================================================
# EMAIL SETTINGS
# ===========================================================
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', 'noreply@heartsound.ai')

# ===========================================================
# SESSION AND SECURITY
# ===========================================================
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_PROXY_SSL_HEADER = (
    'HTTP_X_FORWARDED_PROTO',
    'https'
)

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# ===========================================================
# LOGGING
# ===========================================================
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
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
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'heart_analysis': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'chatbot': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ===========================================================
# DJANGO REST FRAMEWORK
# ===========================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/hour',
        'user': '100/hour',
    },
}

# ===========================================================
# SITE INFO
# ===========================================================
SITE_NAME = 'HeartSound AI'
SITE_TAGLINE = 'AI-Powered Heart Sound Disease Detection System'
SITE_VERSION = '1.0.0'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
