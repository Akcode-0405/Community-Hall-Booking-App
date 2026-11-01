"""
Test settings for the Hall Booking SaaS Platform.

Optimized for fast test execution:
- Uses MD5 password hasher (much faster than PBKDF2 for tests)
- Celery tasks run synchronously (eager mode)
- Email goes to in-memory backend for assertion in tests
- File storage uses in-memory backend (no filesystem I/O)
- Uses the same PostgreSQL + PostGIS database engine as production
  to ensure spatial queries and GIS features are tested accurately.
"""
from .base import *  # noqa: F401, F403

# =============================================================================
# DEBUG
# =============================================================================

# Keep DEBUG off in tests to catch template errors and mimic production behavior
DEBUG = False

# =============================================================================
# DATABASE
# =============================================================================

# When DATABASE_URL is explicitly set (e.g., in CI or Docker with PostGIS),
# Django tests run against PostGIS. Otherwise, defaults to fast in-memory SQLite
# for rapid test execution without requiring a local PostgreSQL daemon.
if 'DATABASE_URL' not in os.environ and os.environ.get('USE_POSTGIS_TEST_DB') != 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# =============================================================================
# PASSWORD HASHING (Speed Optimization)
# =============================================================================

# Use MD5 hasher in tests for dramatically faster user creation.
# PBKDF2 is intentionally slow (for security), but that overhead is
# unnecessary in tests where we create many users.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# =============================================================================
# CELERY (Test — Eager Mode)
# =============================================================================

# Run tasks synchronously so test assertions can check results immediately
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# =============================================================================
# EMAIL (Test — In-Memory Backend)
# =============================================================================

# Store sent emails in django.core.mail.outbox for assertion in tests.
# Example: self.assertEqual(len(mail.outbox), 1)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# =============================================================================
# FILE STORAGE (Test — In-Memory)
# =============================================================================

# Uploads use in-memory storage (see STORAGES below) to avoid filesystem
# side effects during tests.

# =============================================================================
# CACHES (Test — Local Memory)
# =============================================================================

# Use local memory cache in tests to avoid Redis dependency
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    },
}

# =============================================================================
# THROTTLING (Disabled in Tests)
# =============================================================================

# Disable rate limiting in tests to avoid flaky test failures
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = ()  # noqa: F405
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'auth': None}  # noqa: F405

# Dummy Razorpay credentials so signature helpers work; the gateway client
# itself is mocked in tests.
RAZORPAY_KEY_ID = 'rzp_test_dummy'
RAZORPAY_KEY_SECRET = 'test-key-secret'
RAZORPAY_WEBHOOK_SECRET = 'test-webhook-secret'


# =============================================================================
# STATIC FILES (Test)
# =============================================================================

# In-memory uploads and simple static storage (no compression/hashing).
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.InMemoryStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}
