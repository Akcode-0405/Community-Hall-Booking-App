"""
Base abstract models for the Hall Booking SaaS Platform.

This module defines reusable abstract models that enforce consistent patterns
across the entire codebase:

- **UUIDModel**: UUID primary keys on all models (prevents enumeration attacks).
- **TimeStampedModel**: Automatic created_at / updated_at timestamps.
- **BaseModel**: Combines UUID + timestamps (the most commonly inherited model).
- **TenantAwareModel**: Adds a tenant FK with a manager for easy tenant scoping.
- **SoftDeleteModel**: Soft-delete support with custom managers.

Design decisions:
    - UUID4 PKs prevent sequential ID enumeration and simplify cross-tenant
      data merges.
    - Ordering by `-created_at` gives a sensible default everywhere.
    - TenantAwareManager.for_tenant() is the canonical way to scope querysets;
      middleware sets request.tenant but does NOT auto-filter globally (explicit
      is better than implicit).
    - SoftDeleteModel keeps `is_deleted` + `deleted_at` so we can audit who
      deleted what and when, while hiding deleted rows from normal queries.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Managers
# ---------------------------------------------------------------------------


class SoftDeleteManager(models.Manager):
    """
    Default manager for SoftDeleteModel that excludes soft-deleted records.

    Usage:
        MyModel.objects.all()  # only non-deleted rows
        MyModel.all_with_deleted.all()  # includes soft-deleted rows
    """

    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """
    Manager that returns all records including soft-deleted ones.

    Useful for admin views, auditing, and data recovery.
    """

    pass


class TenantAwareManager(models.Manager):
    """
    Manager for tenant-scoped models.

    Provides a convenience method `for_tenant()` to filter by tenant.
    The default queryset is *not* automatically filtered — filtering
    is performed explicitly in views and serializers to maintain
    clarity and testability.
    """

    def get_queryset(self) -> models.QuerySet:
        """Return the standard unfiltered queryset."""
        return super().get_queryset()

    def for_tenant(self, tenant: Any) -> models.QuerySet:
        """
        Return queryset scoped to the given tenant.

        Args:
            tenant: A Tenant model instance or a tenant UUID/PK.

        Returns:
            QuerySet filtered to the specified tenant.
        """
        return self.get_queryset().filter(tenant=tenant)


# ---------------------------------------------------------------------------
# Abstract Models
# ---------------------------------------------------------------------------


class UUIDModel(models.Model):
    """
    Abstract model that provides a UUID v4 primary key.

    All platform models MUST use UUID PKs. This prevents sequential ID
    enumeration, simplifies data import/export across tenants, and plays
    well with distributed systems.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUID v4).",
    )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """
    Abstract model that auto-records creation and last-update timestamps.

    Fields:
        created_at: Set once when the row is first inserted.
        updated_at: Updated every time the row is saved.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when this record was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this record was last updated.",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class BaseModel(UUIDModel, TimeStampedModel):
    """
    Standard abstract base model combining UUID PK + timestamps.

    Most models in the platform should inherit from this.  If the model
    also belongs to a tenant, inherit from `TenantAwareModel` instead
    (which itself inherits BaseModel).
    """

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class TenantAwareModel(BaseModel):
    """
    Abstract model for resources that belong to a specific tenant.

    Adds a required ForeignKey to `tenants.Tenant` and swaps the default
    manager to `TenantAwareManager`.

    Usage in views:
        qs = MyModel.objects.for_tenant(request.tenant)
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
        db_index=True,
        help_text="The tenant this resource belongs to.",
    )

    objects = TenantAwareManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class SoftDeleteModel(models.Model):
    """
    Abstract mixin model providing soft-delete functionality.

    Calling `delete()` on an instance sets `is_deleted=True` and records
    the deletion timestamp rather than removing the row.  Use
    `hard_delete()` when you truly need to remove data (e.g., GDPR
    right-to-erasure).

    Managers:
        objects          — default; excludes soft-deleted rows.
        all_with_deleted — includes soft-deleted rows.

    Can be combined with BaseModel via multiple inheritance:
        class MyModel(BaseModel, SoftDeleteModel):
            ...
    """

    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flag indicating the record has been soft-deleted.",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the record was soft-deleted.",
    )

    objects = SoftDeleteManager()
    all_with_deleted = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using: str | None = None, keep_parents: bool = False) -> None:  # type: ignore[override]
        """
        Soft-delete this instance.

        Sets `is_deleted=True` and `deleted_at` to the current time,
        then saves. Does NOT remove the row from the database.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

    def hard_delete(self, using: str | None = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        """
        Permanently remove this instance from the database.

        Use sparingly — typically only for GDPR erasure requests or
        data cleanup tasks.
        """
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self) -> None:
        """
        Restore a soft-deleted instance.

        Clears `is_deleted` and `deleted_at`, making the record visible
        to the default manager again.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])


# ---------------------------------------------------------------------------
# Concrete models
# ---------------------------------------------------------------------------


class AuditLog(UUIDModel):
    """
    Persistent audit trail for critical domain operations.

    Written via ``apps.common.audit.log_audit_event`` (state transitions,
    tenant suspension, subscription changes, payment events...).

    Design decisions:
        - ``tenant_id`` is a plain UUID, not a FK: the common app must not
          depend on the tenants app, and audit rows must outlive the
          records they describe.
        - ``user`` is SET_NULL for the same reason.
        - ``object_id`` is a string so any primary-key type fits.
    """

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="User who performed the action (null for system/webhook actions).",
    )
    tenant_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Tenant context of the action, if any.",
    )
    action = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Dotted action name, e.g. 'tenant.suspended'.",
    )
    model_name = models.CharField(max_length=100, blank=True, default="")
    object_id = models.CharField(max_length=64, blank=True, default="")
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model_name", "object_id"], name="idx_audit_object"),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.model_name}:{self.object_id}"
