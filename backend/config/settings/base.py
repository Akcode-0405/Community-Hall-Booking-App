"""
Base Django settings for the Hall Booking SaaS Platform.

This file contains settings common to all environments (development,
production, test). Environment-specific settings files import from
this base and override as needed.

Settings are loaded from environment variables using django-environ
for 12-factor app compliance.

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
import os
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import environ

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR points to the 'backend' directory (where manage.py lives).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

# Initialize django-environ and read .env file from the project root
# (one level above BASE_DIR, i.e., the repository root).
env = environ.Env(
    # Default values for environment variables
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    CORS_ALLOWED_ORIGINS=(list, ['http://localhost:3000']),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_PORT=(int, 587),
)

# Read .env file from repository root (parent of backend/)
ENV_FILE = BASE_DIR.parent / '.env'
if ENV_FILE.exists():
    environ.Env.read_env(str(ENV_FILE))

# =============================================================================
# CORE SETTINGS
# =============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY', default='insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DJANGO_DEBUG')

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS')

# Custom platform name used across the application
PLATFORM_NAME = "HallBooking SaaS"

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

# Check if GDAL C library is available (available in Docker container / PostGIS environments)
try:
    from django.contrib.gis.gdal.libgdal import lgdal  # noqa: F401
    HAS_GDAL = True
except Exception:
    HAS_GDAL = False

INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

if HAS_GDAL:
    INSTALLED_APPS.append('django.contrib.gis')  # GeoDjango for PostGIS support

INSTALLED_APPS += [
    # Third-party apps
    'rest_framework',           # Django REST Framework for API development
    'corsheaders',              # Cross-Origin Resource Sharing headers
    'django_filters',           # Filtering support for DRF viewsets
    'drf_spectacular',          # OpenAPI 3.0 schema generation
    'django_extensions',        # Management command extensions and utilities
    'storages',                 # Custom storage backends (S3, etc.)
    'phonenumber_field',        # Phone number model field with validation
    'rest_framework_simplejwt.token_blacklist',  # Refresh-token blacklist (logout, rotation)
    'django_celery_beat',       # Database-backed periodic task scheduler

    # Local apps
    'apps.common',              # Shared utilities, base models, audit log
    'apps.accounts',            # User management, authentication, roles
    'apps.tenants',             # Tenant organisations, memberships, invitations
    # Phase 2 (in progress — not yet registered):
    # 'apps.subscriptions',     # SaaS plans, tenant subscriptions, invoices
    # 'apps.payments',          # Razorpay gateway, signature checks, webhooks
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',             # Must be before CommonMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',         # Serve static files efficiently
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Tenant context for session-authenticated requests (e.g. admin). JWT API
    # requests resolve their tenant in apps.tenants.authentication instead,
    # because DRF authenticates after the middleware chain has run.
    'apps.common.middleware.TenantMiddleware',
    'apps.common.middleware.AuditLogMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# =============================================================================
# AUTHENTICATION
# =============================================================================

# Custom user model: apps.accounts.User with UUID PK and role-based access
AUTH_USER_MODEL = 'accounts.User'

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# PostgreSQL with PostGIS extension for geospatial queries.
# Uses DATABASE_URL env var for 12-factor compliance.
# The PostGIS engine enables GIS model fields and spatial lookups.
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default='postgis://hallbooking:hallbooking@localhost:5432/hallbooking_db',
        engine='django.contrib.gis.db.backends.postgis',
    ),
}

# GeoDjango native libraries. Usually auto-detected; on Apple Silicon with
# Homebrew set e.g. GDAL_LIBRARY_PATH=/opt/homebrew/lib/libgdal.dylib and
# GEOS_LIBRARY_PATH=/opt/homebrew/lib/libgeos_c.dylib in .env.
GDAL_LIBRARY_PATH = env('GDAL_LIBRARY_PATH', default=None)
GEOS_LIBRARY_PATH = env('GEOS_LIBRARY_PATH', default=None)

# Default primary key field type
# All our models use UUIDs explicitly, but this sets the default for
# auto-generated models (e.g., through tables).
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Redis cache backend for session storage, view caching, and rate limiting.
# Using django-redis for full Redis feature support (key expiry, pub/sub, etc.)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'hallbooking',
        'TIMEOUT': 300,  # Default cache timeout: 5 minutes
    },
}

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    # Authentication: JWT via djangorestframework-simplejwt.
    # Note: In Phase 2, this will be updated to apps.tenants.authentication.TenantJWTAuthentication
    # to automatically resolve tenant context from tokens.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    # Default permission: require authentication for all endpoints.
    # Override per-view as needed (e.g., AllowAny for registration).
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

    # Pagination: page-number based with 20 items per page.
    # Clients can request up to 100 items via ?page_size=100.
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,

    # Filtering: django-filter for queryset filtering in list views
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),

    # Exception handling: consistent {"error": {code, message, details}} bodies
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',

    # Schema: use drf-spectacular for OpenAPI 3.0 schema generation
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # Throttling: rate limits to protect against abuse
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',    # Unauthenticated users
        'user': '120/minute',   # Authenticated users
        'auth': '10/minute',    # Login / register / password reset (per IP)
    },

    # Datetime formatting: ISO 8601 for consistency
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
    'DATE_FORMAT': '%Y-%m-%d',
    'TIME_FORMAT': '%H:%M:%S',
}

# =============================================================================
# SIMPLE JWT CONFIGURATION
# =============================================================================

SIMPLE_JWT = {
    # Access tokens expire after 60 minutes; refresh tokens after 7 days
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # Rotate refresh tokens: issue a new refresh token with each refresh request.
    # This limits the window of exposure if a refresh token is compromised.
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,

    # Signing algorithm and key
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,

    # Auth header configuration
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',

    # User identification claim in the JWT payload
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# =============================================================================
# DRF SPECTACULAR (OpenAPI SCHEMA)
# =============================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'Hall Booking SaaS API',
    'DESCRIPTION': (
        'Multi-tenant community hall booking platform API. '
        'Supports tenant management, hall listings, booking workflows, '
        'payment processing via Razorpay, and role-based access control.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,

    # Group endpoints by app/tag for better documentation organization
    'SCHEMA_PATH_PREFIX': r'/api/',

    # Contact and license info
    'CONTACT': {
        'name': 'HallBooking SaaS Support',
    },

    # Component naming
    'COMPONENT_SPLIT_REQUEST': True,
}

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

# Celery uses Redis as both message broker and result backend.
# This keeps the infrastructure simple—one Redis instance serves
# caching, message brokering, and result storage.
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')

# Serialize everything as JSON for security and interoperability
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Use the project's timezone for periodic task scheduling
CELERY_TIMEZONE = 'Asia/Kolkata'

# Enable UTC to avoid DST-related scheduling issues
CELERY_ENABLE_UTC = True

# Periodic tasks. django_celery_beat's DatabaseScheduler syncs these entries
# into the database on start-up, where admins can also tweak them.
from celery.schedules import crontab  # noqa: E402

# Phase 2 entries below are disabled until the subscriptions/tenants task
# modules exist; re-enable by replacing `{} if True else` with nothing.
CELERY_BEAT_SCHEDULE = {} if True else {
    # Move overdue subscriptions through past_due → grace_period → expired
    # and suspend tenants whose grace period has run out.
    'subscriptions-process-lifecycle': {
        'task': 'apps.subscriptions.tasks.process_subscription_lifecycle',
        'schedule': crontab(minute=15, hour='*/1'),
    },
    # Re-check past-due subscriptions against Razorpay in case a webhook
    # was missed (network failure, downtime).
    'subscriptions-reconcile-with-gateway': {
        'task': 'apps.subscriptions.tasks.reconcile_past_due_subscriptions',
        'schedule': crontab(minute=45, hour='*/6'),
    },
    # Remind owners before their subscription renews / expires.
    'subscriptions-send-renewal-reminders': {
        'task': 'apps.subscriptions.tasks.send_renewal_reminders',
        'schedule': crontab(minute=0, hour=9),
    },
    # Expire stale tenant invitations.
    'tenants-expire-invitations': {
        'task': 'apps.tenants.tasks.expire_stale_invitations',
        'schedule': crontab(minute=30, hour=2),
    },
}

# =============================================================================
# FILE STORAGE (S3-COMPATIBLE)
# =============================================================================

# Default file storage uses S3-compatible backend (AWS S3, MinIO, etc.).
# Configured through STORAGES['default'] below (DEFAULT_FILE_STORAGE was
# removed in Django 5.1). Override with the DEFAULT_FILE_STORAGE env var,
# e.g. django.core.files.storage.FileSystemStorage for local development.
DEFAULT_FILE_STORAGE_BACKEND = env(
    'DEFAULT_FILE_STORAGE',
    default='storages.backends.s3boto3.S3Boto3Storage',
)

# AWS S3 / S3-compatible storage settings
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='hallbooking-media')
AWS_S3_ENDPOINT_URL = env('AWS_S3_ENDPOINT_URL', default=None)
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='ap-south-1')
AWS_S3_FILE_OVERWRITE = False  # Don't silently overwrite files with same name
AWS_DEFAULT_ACL = None  # Use bucket default ACL
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 1 day cache for uploaded media
}
AWS_QUERYSTRING_AUTH = True  # Use signed URLs for private media

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

# Email backend is configurable via env var.
# Default: console backend (prints emails to stdout) for development.
EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
DEFAULT_FROM_EMAIL = env(
    'DEFAULT_FROM_EMAIL',
    default='noreply@hallbooking.com',
)

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'en-us'

# Indian Standard Time — the primary market for this platform
TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

# Static files (CSS, JavaScript, Images) served by WhiteNoise
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Project-level static assets (optional directory).
STATICFILES_DIRS = [p for p in [BASE_DIR / 'static'] if p.exists()]

# 'default' = user uploads (S3); 'staticfiles' = WhiteNoise compression.
STORAGES = {
    'default': {
        'BACKEND': DEFAULT_FILE_STORAGE_BACKEND,
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Media files (user-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

# Explicitly list allowed origins for security.
# In development, this can be overridden to allow all origins.
CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS')

# Allow credentials (cookies, auth headers) in cross-origin requests
CORS_ALLOW_CREDENTIALS = True

# Allow the tenant selector header used by multi-tenant staff users.
from corsheaders.defaults import default_headers  # noqa: E402

CORS_ALLOW_HEADERS = (*default_headers, 'x-tenant-id')

# Public URL of the frontend, used to build links in emails
# (password reset, invitations, payment pages).
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:3000')

# =============================================================================
# RAZORPAY PAYMENT GATEWAY
# =============================================================================

# Razorpay API credentials for payment processing
RAZORPAY_KEY_ID = env('RAZORPAY_KEY_ID', default='')
RAZORPAY_KEY_SECRET = env('RAZORPAY_KEY_SECRET', default='')
RAZORPAY_WEBHOOK_SECRET = env('RAZORPAY_WEBHOOK_SECRET', default='')

# =============================================================================
# SUBSCRIPTION BILLING
# =============================================================================

# Days a tenant keeps write access after a failed renewal before the
# subscription expires and the tenant is suspended.
SUBSCRIPTION_GRACE_PERIOD_DAYS = env.int('SUBSCRIPTION_GRACE_PERIOD_DAYS', default=7)

# GST rate (percent). Plan prices are GST-inclusive; invoices show the split.
SUBSCRIPTION_GST_RATE = Decimal(env('SUBSCRIPTION_GST_RATE', default='18'))

# How many billing cycles a Razorpay subscription runs before it completes
# (Razorpay requires a finite total_count).
SUBSCRIPTION_MONTHLY_TOTAL_COUNT = 120   # 10 years of monthly renewals
SUBSCRIPTION_ANNUAL_TOTAL_COUNT = 10     # 10 years of annual renewals

# Send renewal reminders this many days before period end.
SUBSCRIPTION_RENEWAL_REMINDER_DAYS = 3

# Tenant manager invitations expire after this many days.
TENANT_INVITATION_EXPIRY_DAYS = 7

# =============================================================================
# PHONE NUMBER FIELD
# =============================================================================

# Default region for phone number parsing (India)
PHONENUMBER_DEFAULT_REGION = 'IN'
PHONENUMBER_DB_FORMAT = 'E164'

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },

    'loggers': {
        # Django framework logger
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },

        # Application logger — use this in app code:
        # import logging; logger = logging.getLogger('apps')
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },

        # Celery task logger
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },

        # Audit trail (request-level lines from AuditLogMiddleware; domain
        # events are also persisted to the common.AuditLog table).
        'audit': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },

    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}
