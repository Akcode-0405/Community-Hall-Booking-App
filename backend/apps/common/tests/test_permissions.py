"""
Tests for apps.common permission classes.
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from apps.accounts.models import UserRole
from apps.common.permissions import (
    IsActiveSubscription,
    IsCustomer,
    IsOwnerOrReadOnly,
    IsPlatformAdmin,
    IsTenantManager,
    IsTenantMember,
    IsTenantOwner,
    IsVendor,
    TenantResourcePermission,
)


def _mock_request(user=None, membership=None, tenant=None, method="GET"):
    request = MagicMock()
    request.user = user
    request.tenant_membership = membership
    request.tenant = tenant
    request.method = method
    return request


class TestRolePermissions:
    """Test role-based permissions."""

    def test_is_platform_admin(self):
        perm = IsPlatformAdmin()
        admin_user = MagicMock(is_authenticated=True, role=UserRole.PLATFORM_ADMIN)
        customer_user = MagicMock(is_authenticated=True, role=UserRole.CUSTOMER)
        anon_user = MagicMock(is_authenticated=False)

        assert perm.has_permission(_mock_request(admin_user), None) is True
        assert perm.has_permission(_mock_request(customer_user), None) is False
        assert perm.has_permission(_mock_request(anon_user), None) is False

    def test_is_customer(self):
        perm = IsCustomer()
        customer_user = MagicMock(is_authenticated=True, role=UserRole.CUSTOMER)
        vendor_user = MagicMock(is_authenticated=True, role=UserRole.VENDOR)

        assert perm.has_permission(_mock_request(customer_user), None) is True
        assert perm.has_permission(_mock_request(vendor_user), None) is False

    def test_is_vendor(self):
        perm = IsVendor()
        vendor_user = MagicMock(is_authenticated=True, role=UserRole.VENDOR)
        customer_user = MagicMock(is_authenticated=True, role=UserRole.CUSTOMER)

        assert perm.has_permission(_mock_request(vendor_user), None) is True
        assert perm.has_permission(_mock_request(customer_user), None) is False

    def test_tenant_membership_permissions(self):
        owner_perm = IsTenantOwner()
        manager_perm = IsTenantManager()
        member_perm = IsTenantMember()

        user = MagicMock(is_authenticated=True)
        owner_m = MagicMock(role="owner")
        manager_m = MagicMock(role="manager")

        # Owner
        assert owner_perm.has_permission(_mock_request(user, membership=owner_m), None) is True
        assert manager_perm.has_permission(_mock_request(user, membership=owner_m), None) is False
        assert member_perm.has_permission(_mock_request(user, membership=owner_m), None) is True

        # Manager
        assert owner_perm.has_permission(_mock_request(user, membership=manager_m), None) is False
        assert manager_perm.has_permission(_mock_request(user, membership=manager_m), None) is True
        assert member_perm.has_permission(_mock_request(user, membership=manager_m), None) is True


class TestObjectPermissions:
    """Test object-level and tenant isolation permissions."""

    def test_is_owner_or_read_only(self):
        perm = IsOwnerOrReadOnly()
        user1 = MagicMock(is_authenticated=True)
        user2 = MagicMock(is_authenticated=True)
        obj = MagicMock(user=user1)

        # Safe methods (GET, HEAD, OPTIONS) allowed for anyone
        assert perm.has_object_permission(_mock_request(user2, method="GET"), None, obj) is True

        # Unsafe methods allowed only for owner
        assert perm.has_object_permission(_mock_request(user1, method="PATCH"), None, obj) is True
        assert perm.has_object_permission(_mock_request(user2, method="PATCH"), None, obj) is False

    def test_tenant_resource_permission(self):
        perm = TenantResourcePermission()
        tenant1_id = uuid.uuid4()
        tenant2_id = uuid.uuid4()

        tenant1 = MagicMock(pk=tenant1_id)
        tenant2 = MagicMock(pk=tenant2_id)

        obj = MagicMock(tenant_id=tenant1_id)
        user = MagicMock(is_authenticated=True, role="tenant_manager")

        # User in Tenant 1 accessing Tenant 1 resource -> OK
        assert perm.has_object_permission(_mock_request(user, tenant=tenant1), None, obj) is True

        # User in Tenant 2 accessing Tenant 1 resource -> FORBIDDEN
        assert perm.has_object_permission(_mock_request(user, tenant=tenant2), None, obj) is False

        # Platform admin bypasses check
        admin_user = MagicMock(is_authenticated=True, role=UserRole.PLATFORM_ADMIN)
        assert perm.has_object_permission(_mock_request(admin_user, tenant=tenant2), None, obj) is True

