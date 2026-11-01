"""
Development settings for the Hall Booking SaaS Platform.

These settings are optimized for local development:
- DEBUG is enabled for detailed error pages
- All CORS origins are allowed for frontend dev servers
- Email is printed to console instead of sent
- Celery tasks run synchronously (eager mode) for easier debugging
- Django Debug Toolbar is available for query inspection

NEVER use these settings in production!
"""
from .base import *  # noqa: F401, F403

# =============================================================================
# DEBUG
# =============================================================================

DEBUG = True

ALLOWED_HOSTS = ['*']

# =============================================================================
# INSTALLED APPS (Development Additions)
# =============================================================================

INSTALLED_APPS += [
    'debug_toolbar',
]

# =============================================================================
# MIDDLEWARE (Development Additions)
# =============================================================================

# Debug toolbar middleware must be inserted early to capture all queries.
# It should come after any encoding middleware but before most others.
MIDDLEWARE.insert(
    MIDDLEWARE.index('django.middleware.common.CommonMiddleware'),
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

# =============================================================================
# DEBUG TOOLBAR
# =============================================================================

# Show debug toolbar for requests from these IPs
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Docker-compatible: also match the Docker gateway IP
import socket
try:
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]
except socket.gaierror:
    pass

# =============================================================================
# CACHE (Development)
# =============================================================================

# In-memory cache by default so local development doesn't need Redis
# (DRF throttling stores its counters in the cache). Set
# DEV_USE_REDIS_CACHE=True to use the Redis cache from base.py instead.
if not env.bool('DEV_USE_REDIS_CACHE', default=False):  # noqa: F405
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'hallbooking-dev',
        },
    }

# =============================================================================
# CORS (Development — Allow All)
# =============================================================================

# In development, allow requests from any origin for convenience.
# This is overridden in production where only explicit origins are allowed.
CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# EMAIL (Development — Console Backend)
# =============================================================================

# Print emails to stdout instead of sending them
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# =============================================================================
# CELERY (Development — Eager Mode)
# =============================================================================

# Execute tasks synchronously in the calling process.
# This avoids needing a running Celery worker during development
# and makes debugging easier (breakpoints work, exceptions propagate).
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# =============================================================================
# LOGGING (Development — Verbose)
# =============================================================================

# Show SQL queries in the console during development
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'WARNING',  # Set to 'DEBUG' to see all SQL queries
    'propagate': False,
}

# =============================================================================
# STATIC FILES (Development)
# =============================================================================

# Local filesystem uploads unless DEFAULT_FILE_STORAGE points at S3/MinIO;
# standard static file storage (no compression/hashing).
STORAGES = {
    'default': {
        'BACKEND': env(  # noqa: F405
            'DEFAULT_FILE_STORAGE',
            default='django.core.files.storage.FileSystemStorage',
        ),
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}
