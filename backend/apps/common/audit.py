"""
Audit logging helpers.

``log_audit_event`` records a domain event both to the ``audit`` logger
(for log shipping) and to the ``AuditLog`` table (for in-app querying).
Call it from the service layer for critical operations: state transitions,
suspensions, plan changes, payment events, membership changes.
"""

from __future__ import annotations

import logging
from typing import Any

audit_logger = logging.getLogger("audit")


def log_audit_event(
    *,
    user: Any | None,
    tenant: Any | None,
    action: str,
    resource_type: str,
    resource_id: Any | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """
    Record a custom audit event.

    Args:
        user: The user performing the action (``None`` for system actions).
        tenant: The tenant context (instance or ``None``).
        action: Short dotted name, e.g. ``"booking.approved"``.
        resource_type: Model name, e.g. ``"Booking"``.
        resource_id: PK of the affected resource.
        details: Additional JSON-serialisable data.
        ip_address: Client IP if available.
    """
    from apps.common.models import AuditLog  # noqa: WPS433 — avoid import cycles

    details = details or {}
    audit_logger.info(
        "AUDIT_EVENT | action=%s resource=%s:%s user=%s tenant=%s ip=%s details=%s",
        action,
        resource_type,
        resource_id,
        getattr(user, "pk", None),
        getattr(tenant, "pk", None),
        ip_address,
        details,
    )
    AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        tenant_id=getattr(tenant, "pk", None),
        action=action,
        model_name=resource_type,
        object_id=str(resource_id) if resource_id is not None else "",
        changes=details,
        ip_address=ip_address,
    )
