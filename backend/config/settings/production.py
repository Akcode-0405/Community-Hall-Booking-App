"""
Production settings for the Hall Booking SaaS Platform.

These settings are hardened for production deployment:
- DEBUG is disabled
- Strict security headers (HSTS, secure cookies, SSL redirect)
- Sentry integration for error tracking
- Only explicitly listed hosts are allowed

Ensure all environment variables are properly set before deploying.
"""
import sentry_sdk

from .base import *  # noqa: F401, F403

# =============================================================================
# CORE SETTINGS
# =============================================================================

DEBUG = False

# Only serve requests for explicitly allowed hostnames.
# Set via DJANGO_ALLOWED_HOSTS env var (comma-separated list).
ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS')  # noqa: F405

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# Redirect all HTTP requests to HTTPS (except the container health probe)
# Set DJANGO_SECURE_SSL_REDIRECT=False only when TLS terminates elsewhere and
# internal HTTP calls (e.g. frontend → backend inside docker compose) must work.
SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)  # noqa: F405
SECURE_REDIRECT_EXEMPT = [r'^api/health/$']

# HTTP Strict Transport Security (HSTS)
# Tell browsers to only use HTTPS for this domain for 1 year.
# Enable subdomains and preloading once confirmed working.
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Prevent the browser from MIME-sniffing the content type
SECURE_CONTENT_TYPE_NOSNIFF = True

# Only send cookies over HTTPS connections. DJANGO_SECURE_COOKIES=False is
# for the local docker-compose stack served over plain HTTP.
SESSION_COOKIE_SECURE = env.bool('DJANGO_SECURE_COOKIES', default=True)  # noqa: F405
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE

# Use HttpOnly flag on session cookies (prevents JavaScript access)
SESSION_COOKIE_HTTPONLY = True

# Set SameSite attribute on cookies for CSRF protection
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

# Referrer policy — don't leak full URLs in Referer headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# X-Frame-Options — prevent clickjacking
X_FRAME_OPTIONS = 'DENY'

# Proxy SSL header — if behind a reverse proxy (e.g., Nginx, ALB)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =============================================================================
# SENTRY ERROR TRACKING
# =============================================================================

SENTRY_DSN = env('SENTRY_DSN', default='')  # noqa: F405

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Set traces_sample_rate to capture a percentage of transactions
        # for performance monitoring. Adjust in production based on volume.
        traces_sample_rate=0.1,
        # Send user info (ID, email) with error reports for debugging.
        # PII is only sent to Sentry, not exposed publicly.
        send_default_pii=True,
        # Associate errors with the correct release version
        environment='production',
    )

# =============================================================================
# LOGGING (Production)
# =============================================================================

# In production, set a higher log level to reduce noise
LOGGING['loggers']['django']['level'] = 'WARNING'  # noqa: F405
LOGGING['loggers']['apps']['level'] = 'INFO'  # noqa: F405
LOGGING['loggers']['celery']['level'] = 'WARNING'  # noqa: F405
