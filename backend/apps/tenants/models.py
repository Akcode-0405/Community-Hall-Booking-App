"""
Tenant models for the Hall Booking SaaS Platform.

Design decisions:
    - **Shared schema + tenant FK.** ``Tenant`` is the isolation boundary;
      every tenant-owned model (locations, halls, bookings...) carries a
      ``tenant`` FK via ``apps.common.models.TenantAwareModel``.
    - **Membership is the source of truth for tenant roles.** ``User.role``
      says what *kind* of user someone is (used for routing / UI);
      ``TenantMembership.role`` says what they may do *in a given tenant*.
      Permission classes check the membership.
    - **Suspension reason is recorded.** A tenant suspended for non-payment
      is reactivated automatically when payment succeeds; one suspended by a
      platform admin is not.
    - **Invitations store a token hash**, never the raw token, so a leaked
      database row cannot be used to accept an invitation.
"""
from __future__ import annotations

import hashlib
import secrets
from typing import Any

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField

from apps.common.models import BaseModel
from apps.common.validators import PinCodeValidator


class TenantStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'
    CANCELLED = 'cancelled', 'Cancelled'


class SuspensionReason(models.TextChoices):
    NONE = '', 'None'
    ADMIN = 'admin', 'Suspended by platform admin'
    NON_PAYMENT = 'non_payment', 'Subscription expired (non-payment)'


class Tenant(BaseModel):
    """A hall-owning business that subscribes to the platform."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    business_registration_number = models.CharField(max_length=100, blank=True, default='')
    gstin = models.CharField('GSTIN', max_length=15, blank=True, default='')
    contact_email = models.EmailField()
    contact_phone = PhoneNumberField(blank=True, null=True, region='IN')

    # Registered business address (shown on invoices).
    address_line_1 = models.CharField(max_length=255, blank=True, default='')
    address_line_2 = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    pin_code = models.CharField(
        max_length=6, blank=True, default='', validators=[PinCodeValidator()]
    )

    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.ACTIVE,
        db_index=True,
    )
    suspension_reason = models.CharField(
        max_length=20,
        choices=SuspensionReason.choices,
        blank=True,
        default=SuspensionReason.NONE,
    )
    suspension_note = models.TextField(blank=True, default='')
    suspended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tenants'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self) -> str:
        base = slugify(self.name)[:200] or 'tenant'
        slug = base
        while Tenant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{secrets.token_hex(3)}"
        return slug

    # ------------------------------------------------------------------ #
    # Subscription helpers
    # ------------------------------------------------------------------ #
    @property
    def current_subscription(self) -> Any | None:
        """The tenant's live (non-terminal) subscription, if any."""
        cached = getattr(self, '_current_subscription_cache', models.NOT_PROVIDED)
        if cached is not models.NOT_PROVIDED:
            return cached
        from django.apps import apps as django_apps  # noqa: WPS433

        if not django_apps.is_installed('apps.subscriptions'):
            # Phase 2 billing not installed yet: no subscription exists.
            self._current_subscription_cache = None
            return None
        from apps.subscriptions.models import LIVE_STATUSES  # noqa: WPS433

        sub = (
            self.subscriptions.filter(status__in=LIVE_STATUSES)
            .select_related('plan', 'scheduled_plan')
            .first()
        )
        self._current_subscription_cache = sub
        return sub

    def clear_subscription_cache(self) -> None:
        self.__dict__.pop('_current_subscription_cache', None)

    def write_block_reason(self) -> str | None:
        """
        Why this tenant may not modify business data right now, or ``None``.

        Business writes require an active tenant AND a subscription in a
        status that grants write access (active / past_due / grace_period).
        """
        if self.status == TenantStatus.SUSPENDED:
            return 'This tenant account is suspended. Write operations are not permitted.'
        if self.status == TenantStatus.CANCELLED:
            return 'This tenant account has been cancelled.'
        from django.apps import apps as django_apps
        if not django_apps.is_installed('apps.subscriptions'):
            return None if self.status == TenantStatus.ACTIVE else 'Tenant is not active.'
        sub = self.current_subscription
        if sub is None or not sub.grants_write_access:
            return (
                'An active subscription is required to perform this operation. '
                'Please subscribe or renew your plan.'
            )
        return None

    @property
    def can_write(self) -> bool:
        return self.write_block_reason() is None


class MembershipRole(models.TextChoices):
    OWNER = 'owner', 'Owner'
    MANAGER = 'manager', 'Manager'


class TenantMembership(BaseModel):
    """Links a user to a tenant with an owner or manager role."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant_memberships',
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    role = models.CharField(max_length=20, choices=MembershipRole.choices)
    is_active = models.BooleanField(default=True, db_index=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'tenant_memberships'
        ordering = ['joined_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'tenant'], name='uniq_membership_user_tenant'
            ),
        ]
        indexes = [
            models.Index(fields=['tenant', 'role', 'is_active'], name='idx_membership_tenant_role'),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.tenant} ({self.role})"


class InvitationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    REVOKED = 'revoked', 'Revoked'
    EXPIRED = 'expired', 'Expired'


class TenantInvitation(BaseModel):
    """
    An invitation for someone to join a tenant as a manager.

    The raw token is only ever emailed; the database stores its SHA-256.
    """

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(
        max_length=20, choices=MembershipRole.choices, default=MembershipRole.MANAGER
    )
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
        db_index=True,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )

    class Meta:
        db_table = 'tenant_invitations'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'email'],
                condition=Q(status='pending'),
                name='uniq_pending_invitation_per_email',
            ),
        ]

    def __str__(self) -> str:
        return f"Invitation {self.email} → {self.tenant} ({self.status})"

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(32)

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at
