"""
DRF permission classes for the Hall Booking SaaS Platform.

Permission class hierarchy and usage guide:

    ┌────────────────────────────────┐
    │   IsPlatformAdmin              │  Global: Full access to everything.
    ├────────────────────────────────┤
    │   IsTenantOwner                │  Tenant: Owner of the current tenant.
    │   IsTenantManager              │  Tenant: Manager within current tenant.
    │   IsTenantMember               │  Tenant: Owner OR Manager.
    ├────────────────────────────────┤
    │   IsCustomer                   │  Role: Authenticated customer.
    │   IsVendor                     │  Role: Authenticated vendor.
    ├────────────────────────────────┤
    │   IsOwnerOrReadOnly            │  Object: Owner can write; others read.
    │   TenantResourcePermission     │  Object: Resource must belong to tenant.
    ├────────────────────────────────┤
    │   IsActiveSubscription         │  Subscription: Block writes when lapsed.
    └────────────────────────────────┘

Tenant-level checks rely on ``request.tenant`` and
``request.tenant_membership``, which are set by
``apps.tenants.authentication.TenantJWTAuthentication`` (API) or
``TenantMiddleware`` (session). The membership — not ``User.role`` — is the
source of truth for whether someone is an owner or manager *of this tenant*.

Combine permissions in views with ``|`` (OR) and ``&`` (AND)::

    permission_classes = [IsAuthenticated, IsTenantOwner | IsPlatformAdmin]
"""

from __future__ import annotations

import logging
from typing import Any

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

logger = logging.getLogger(__name__)


def _is_authenticated(request: Request) -> bool:
    return bool(request.user and request.user.is_authenticated)


def _membership(request: Request) -> Any | None:
    """Return the active membership resolved for this request, if any."""
    return getattr(request, "tenant_membership", None)


# ---------------------------------------------------------------------------
# Role-based permissions
# ---------------------------------------------------------------------------


class IsPlatformAdmin(BasePermission):
    """
    Allow access only to users with the ``platform_admin`` role.

    Platform admins have god-mode access across all tenants.  Use this
    sparingly and always pair with proper audit logging.
    """

    message = "Platform admin access required."

    def has_permission(self, request: Request, view: Any) -> bool:
        return _is_authenticated(request) and getattr(
            request.user, "role", None
        ) == "platform_admin"


class IsTenantOwner(BasePermission):
    """
    Allow access to users holding an active **owner** membership in the
    request's tenant.
    """

    message = "Tenant owner access required."

    def has_permission(self, request: Request, view: Any) -> bool:
        if not _is_authenticated(request):
            return False
        membership = _membership(request)
        return membership is not None and membership.role == "owner"


class IsTenantManager(BasePermission):
    """
    Allow access to users holding an active **manager** membership in the
    request's tenant.

    Managers have narrower access than owners (no billing or member
    management). Location/hall-level scoping arrives with Phase 3.
    """

    message = "Tenant manager access required."

    def has_permission(self, request: Request, view: Any) -> bool:
        if not _is_authenticated(request):
            return False
        membership = _membership(request)
        return membership is not None and membership.role == "manager"


class IsTenantMember(BasePermission):
    """Allow access to any active member (owner or manager) of the request's tenant."""

    message = "Tenant member (owner or manager) access required."

    def has_permission(self, request: Request, view: Any) -> bool:
        return _is_authenticated(request) and _membership(request) is not None


class IsCustomer(BasePermission):
    """Allow access only to authenticated users with the ``customer`` role."""

    message = "Customer access required."

    def has_permission(self, request: Request, view: Any) -> bool:
        return _is_authenticated(request) and getattr(
            request.user, "role", None
        ) == "customer"


class IsVendor(BasePermission):
    """Allow access only to authenticated users with the ``vendor`` role."""

    message = "Vendor access required."

    def has_permission(self, request: Request, view: Any) -> bool:
        return _is_authenticated(request) and getattr(
            request.user, "role", None
        ) == "vendor"


# ---------------------------------------------------------------------------
# Object-level permissions
# ---------------------------------------------------------------------------


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: only the owner of an object may modify it.

    Looks for a ``user``, ``customer``, ``created_by`` or ``owner`` field on
    the object and compares it to ``request.user``.  Read-only methods are
    always allowed.
    """

    OWNER_FIELDS = ("user", "customer", "created_by", "owner")

    message = "You do not have permission to modify this resource."

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        for field_name in self.OWNER_FIELDS:
            owner = getattr(obj, field_name, None)
            if owner is not None:
                return owner == request.user
        return False


class TenantResourcePermission(BasePermission):
    """
    Object-level permission ensuring a resource belongs to the request's
    tenant. Prevents a member of Tenant A from touching Tenant B's data even
    if they guess a UUID.

    Platform admins bypass tenant scoping.
    """

    message = "You do not have permission to access this tenant's resources."

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        if getattr(request.user, "role", None) == "platform_admin":
            return True

        request_tenant = getattr(request, "tenant", None)
        if request_tenant is None:
            return False

        obj_tenant_id = getattr(obj, "tenant_id", None)
        if obj_tenant_id is None:
            # Not a tenant-scoped resource.
            return True

        if obj_tenant_id != request_tenant.pk:
            logger.warning(
                "Cross-tenant access attempt: user=%s tried to access "
                "resource %s.%s (tenant=%s) from tenant=%s",
                request.user.pk,
                type(obj).__name__,
                obj.pk,
                obj_tenant_id,
                request_tenant.pk,
            )
            return False

        # TODO (Phase 3): restrict managers to assigned locations/halls.
        return True


# ---------------------------------------------------------------------------
# Subscription permission
# ---------------------------------------------------------------------------


class IsActiveSubscription(BasePermission):
    """
    Block write operations for tenants that are suspended or have no
    subscription granting write access (active, past-due or in grace).

    - Read operations are always allowed so lapsed tenants can see data.
    - Requests without a tenant context (customers, vendors) pass through.
    - Platform admins bypass the check.

    Use it on every endpoint that modifies tenant business data (locations,
    halls, pricing, bookings, members). Do *not* use it on billing
    endpoints — a lapsed tenant must still be able to pay.
    """

    message = (
        "An active subscription is required to perform this operation. "
        "Please renew your subscription."
    )

    def has_permission(self, request: Request, view: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        if getattr(request.user, "role", None) == "platform_admin":
            return True

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return True

        reason = tenant.write_block_reason()
        if reason is not None:
            self.message = reason
            return False
        return True
