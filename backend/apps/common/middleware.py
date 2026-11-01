"""
Middleware for the Hall Booking SaaS Platform.

Provides:
- **TenantMiddleware**: Attaches tenant context to each request (see the
  class docstring for how this interacts with JWT authentication).
- **AuditLogMiddleware**: Logs critical write operations for audit trails.

Both middlewares run AFTER Django's AuthenticationMiddleware.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Callable

from django.http import HttpRequest, HttpResponse

if TYPE_CHECKING:
    pass

logger = logging.getLogger("apps.common.middleware")
audit_logger = logging.getLogger("audit")


# ---------------------------------------------------------------------------
# Tenant Middleware
# ---------------------------------------------------------------------------


class TenantMiddleware:
    """
    Attach tenant context to every request.

    Sets ``request.tenant`` and ``request.tenant_membership`` (both ``None``
    by default) using ``apps.tenants.context.resolve_tenant_context``.

    Important: Django middleware runs *before* DRF authenticates a JWT, so
    for API requests ``request.user`` is still anonymous here. API requests
    get their tenant from ``apps.tenants.authentication.TenantJWTAuthentication``,
    which calls the same resolver right after authenticating. This
    middleware covers session-authenticated requests (Django admin) and
    guarantees the attributes always exist.

    Write-blocking for suspended tenants / lapsed subscriptions is enforced
    at the API layer by ``IsActiveSubscription`` and the service layer —
    not here — because the user (and therefore the tenant) is unknown at
    this point for JWT requests.

    Behaviour by role:
        - tenant_owner / tenant_manager: tenant from their active
          TenantMembership; ``X-Tenant-ID`` selects one when they have several.
        - platform_admin: no tenant unless ``X-Tenant-ID`` is sent.
        - customer / vendor / anonymous: no tenant.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            from apps.tenants.context import resolve_tenant_context  # noqa: WPS433
            resolve_tenant_context(request, getattr(request, "user", None))
        except (ImportError, ModuleNotFoundError):
            request.tenant = None
            request.tenant_membership = None
        return self.get_response(request)


# ---------------------------------------------------------------------------
# Audit Log Middleware
# ---------------------------------------------------------------------------


class AuditLogMiddleware:
    """
    Log critical write operations for audit and compliance.

    Captures:
        - User ID and role
        - Tenant ID (if resolved)
        - Client IP address
        - HTTP method and path
        - Response status code
        - Request duration

    Only POST, PUT, PATCH, and DELETE requests are logged.  GET / HEAD /
    OPTIONS are skipped to keep the audit log focused and manageable.

    Logs go to the ``audit`` logger which should be configured in Django
    settings to write to a dedicated file or external service.

    Usage in settings.py::

        MIDDLEWARE = [
            ...
            'apps.common.middleware.AuditLogMiddleware',
        ]

        LOGGING = {
            ...
            'loggers': {
                'audit': {
                    'handlers': ['audit_file'],
                    'level': 'INFO',
                },
            },
        }
    """

    AUDITED_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method not in self.AUDITED_METHODS:
            return self.get_response(request)

        start_time = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start_time) * 1000

        self._log_request(request, response, duration_ms)

        return response

    def _log_request(
        self,
        request: HttpRequest,
        response: HttpResponse,
        duration_ms: float,
    ) -> None:
        """Write a structured audit log entry."""
        from apps.common.utils import get_client_ip  # noqa: WPS433

        user = getattr(request, "user", None)
        tenant = getattr(request, "tenant", None)

        audit_logger.info(
            "AUDIT | method=%s path=%s status=%s user=%s role=%s "
            "tenant=%s ip=%s duration_ms=%.1f",
            request.method,
            request.path,
            response.status_code,
            getattr(user, "pk", "anonymous"),
            getattr(user, "role", "unknown"),
            getattr(tenant, "pk", None),
            get_client_ip(request),
            duration_ms,
        )


# Backwards-compatible re-export: the persistent implementation lives in
# apps.common.audit.
from apps.common.audit import log_audit_event  # noqa: E402,F401
