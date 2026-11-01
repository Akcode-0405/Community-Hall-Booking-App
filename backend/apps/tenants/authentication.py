"""
JWT authentication that also resolves tenant context.

Why this exists: Django middleware runs before DRF authenticates a JWT, so
``TenantMiddleware`` only ever sees an anonymous user on API requests.
Resolving the tenant here — immediately after the token is validated —
guarantees ``request.tenant`` is correct before any permission check runs.
"""
from __future__ import annotations

from typing import Any

from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication

from .context import resolve_tenant_context


class TenantJWTAuthentication(JWTAuthentication):
    """SimpleJWT authentication + tenant context resolution."""

    def authenticate(self, request: Request) -> tuple[Any, Any] | None:
        result = super().authenticate(request)
        if result is not None:
            user, _token = result
            resolve_tenant_context(request._request, user)
        return result
