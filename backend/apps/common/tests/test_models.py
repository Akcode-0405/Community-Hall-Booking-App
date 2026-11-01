"""
Tests for apps.common models and managers.
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from django.db import models
from django.utils import timezone

from apps.common.models import (
    AllObjectsManager,
    AuditLog,
    SoftDeleteManager,
    SoftDeleteModel,
    TenantAwareManager,
)


class DummySoftDeletable:
    """Mock class simulating SoftDeleteModel behavior without DB table."""

    def __init__(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save_called = False
        self.save_kwargs = {}

    def save(self, **kwargs):
        self.save_called = True
        self.save_kwargs = kwargs

    def delete(self, using=None, keep_parents=False):
        SoftDeleteModel.delete(self, using=using, keep_parents=keep_parents)

    def restore(self):
        SoftDeleteModel.restore(self)


@pytest.mark.django_db
class TestAuditLogModel:
    """Test suite for AuditLog model (inherits from UUIDModel)."""

    def test_uuid_generation_on_audit_log(self):
        """AuditLog automatically generates a UUID4 PK."""
        log = AuditLog.objects.create(
            action="tenant.suspended",
            model_name="Tenant",
            object_id="12345678-1234-5678-1234-567812345678",
            changes={"status": ["active", "suspended"]},
            ip_address="127.0.0.1",
        )
        assert isinstance(log.id, uuid.UUID)
        assert log.created_at is not None
        assert "tenant.suspended Tenant:12345678-1234-5678-1234-567812345678" in str(log)


class TestSoftDeleteMethods:
    """Unit tests for SoftDeleteModel methods."""

    def test_soft_delete(self):
        instance = DummySoftDeletable()
        assert instance.is_deleted is False
        assert instance.deleted_at is None

        instance.delete()
        assert instance.is_deleted is True
        assert instance.deleted_at is not None
        assert instance.save_called is True
        assert "is_deleted" in instance.save_kwargs["update_fields"]

    def test_restore(self):
        instance = DummySoftDeletable()
        instance.delete()
        assert instance.is_deleted is True

        instance.restore()
        assert instance.is_deleted is False
        assert instance.deleted_at is None
        assert instance.save_called is True
        assert "is_deleted" in instance.save_kwargs["update_fields"]


class TestTenantAwareManager:
    """Unit tests for TenantAwareManager queryset methods."""

    def test_for_tenant_filter_applied(self):
        manager = TenantAwareManager()
        mock_qs = MagicMock()
        manager.get_queryset = MagicMock(return_value=mock_qs)

        tenant_uuid = uuid.uuid4()
        manager.for_tenant(tenant_uuid)

        mock_qs.filter.assert_called_once_with(tenant=tenant_uuid)


class TestSoftDeleteManager:
    """Unit tests for SoftDeleteManager queryset methods."""

    def test_soft_delete_manager_excludes_deleted(self):
        manager = SoftDeleteManager()
        mock_super_qs = MagicMock()

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(models.Manager, "get_queryset", lambda self: mock_super_qs)
            manager.get_queryset()
            mock_super_qs.filter.assert_called_once_with(is_deleted=False)
