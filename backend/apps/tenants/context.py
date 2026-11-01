"""
Tenant context resolution.

A single function, ``resolve_tenant_context``, decides which tenant a
request acts on. It is called from:

    - ``TenantJWTAuthentication`` right after a JWT is authenticated
      (API requests), and
    - ``TenantMiddleware`` (session-authenticated requests such as the
      Django admin).

It sets two attributes on the Django ``HttpRequest``:

    request.tenant             Tenant | None
    request.tenant_membership  TenantMembership | None (None for admins)

DRF's ``Request`` proxies unknown attributes to the wrapped ``HttpRequest``,
so views and permissions can read ``request.tenant`` directly.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

TENANT_HEADER = 'HTTP_X_TENANT_ID'


def _header_tenant_id(request: Any) -> uuid.UUID | None | bool:
    """
    Parse the ``X-Tenant-ID`` header.

    Returns the UUID, ``None`` if absent, or ``False`` if present but
    malformed (which must resolve to *no* tenant, never a default one).
    """
    raw = request.META.get(TENANT_HEADER)
    if not raw:
        return None
    try:
        return uuid.UUID(str(raw))
    except ValueError:
        return False


def resolve_tenant_context(request: Any, user: Any) -> None:
    """Attach ``tenant`` and ``tenant_membership`` to ``request``."""
    from apps.tenants.models import Tenant, TenantMembership  # noqa: WPS433

    request.tenant = None
    request.tenant_membership = None

    if user is None or not getattr(user, 'is_authenticated', False):
        return

    header_id = _header_tenant_id(request)
    if header_id is False:
        logger.info('Malformed X-Tenant-ID header from user %s', user.pk)
        return

    role = getattr(user, 'role', None)

    if role == 'platform_admin':
        # Admins have no implicit tenant; they may scope explicitly.
        if header_id:
            request.tenant = Tenant.objects.filter(pk=header_id).first()
        return

    if role not in ('tenant_owner', 'tenant_manager'):
        return

    memberships = TenantMembership.objects.filter(
        user=user, is_active=True
    ).select_related('tenant')
    if header_id:
        memberships = memberships.filter(tenant_id=header_id)

    membership = memberships.order_by('joined_at').first()
    if membership is None:
        logger.info(
            'User %s (role=%s) has no active membership matching the request.',
            user.pk,
            role,
        )
        return

    request.tenant = membership.tenant
    request.tenant_membership = membership
