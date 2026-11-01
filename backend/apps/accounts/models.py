"""
User model for the Hall Booking SaaS Platform.

Design Decisions:
- Email-based authentication (no username field).
- Single User table with role field instead of separate tables per role.
  This simplifies queries and avoids multi-table inheritance issues.
- UUID primary key for security (non-guessable IDs prevent enumeration).
- Phone number stored using django-phonenumber-field for proper E.164 validation.
- Profile fields (first_name, last_name, city, state) stored directly on User
  to keep things simple and avoid an extra JOIN for the most common query.
- Avatar stored as URL (pointing to S3/external storage).
- CustomerPreference is a separate model (OneToOne) since it's only relevant
  for customers and contains recommendation engine weights.
- FavouriteHall uses a raw UUIDField for hall_id instead of ForeignKey because
  the halls app doesn't exist yet (Phase 3). This will be migrated to a proper
  FK in that phase.
"""
from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from .managers import UserManager


class UserRole(models.TextChoices):
    """
    Enumeration of all user roles in the platform.

    - PLATFORM_ADMIN: Full platform access, manages tenants.
    - TENANT_OWNER: Owns one or more tenants (hall owners).
    - TENANT_MANAGER: Manages a tenant on behalf of the owner.
    - CUSTOMER: Books halls, leaves reviews.
    - VENDOR: Provides services (catering, decoration, etc.).
    """

    PLATFORM_ADMIN = 'platform_admin', 'Platform Admin'
    TENANT_OWNER = 'tenant_owner', 'Tenant Owner'
    TENANT_MANAGER = 'tenant_manager', 'Tenant Manager'
    CUSTOMER = 'customer', 'Customer'
    VENDOR = 'vendor', 'Vendor'


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model using email for authentication.

    Inherits from AbstractBaseUser for full control over authentication,
    and PermissionsMixin for Django's built-in permission framework
    (groups, user_permissions, is_superuser).
    """

    # ------------------------------------------------------------------ #
    # Primary key & identity
    # ------------------------------------------------------------------ #
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(
        'Email Address',
        unique=True,
        db_index=True,
    )
    phone = PhoneNumberField(
        'Phone Number',
        blank=True,
        null=True,
        region='IN',
        help_text='Phone number in E.164 format (e.g. +919876543210).',
    )

    # ------------------------------------------------------------------ #
    # Personal information
    # ------------------------------------------------------------------ #
    first_name = models.CharField('First Name', max_length=150)
    last_name = models.CharField('Last Name', max_length=150)
    role = models.CharField(
        'Role',
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
    )
    avatar_url = models.URLField('Avatar URL', blank=True, null=True)

    # ------------------------------------------------------------------ #
    # Address fields (primarily for customers)
    # ------------------------------------------------------------------ #
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')

    # ------------------------------------------------------------------ #
    # Status flags
    # ------------------------------------------------------------------ #
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user should be treated as active.',
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into the admin site.',
    )
    is_email_verified = models.BooleanField(
        default=False,
        help_text='Whether the user has verified their email address.',
    )
    is_phone_verified = models.BooleanField(
        default=False,
        help_text='Whether the user has verified their phone number.',
    )

    # ------------------------------------------------------------------ #
    # Timestamps
    # ------------------------------------------------------------------ #
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------------------------------------------------ #
    # Notification preferences
    # ------------------------------------------------------------------ #
    email_notifications = models.BooleanField(
        default=True,
        help_text='Whether the user wants to receive email notifications.',
    )
    sms_notifications = models.BooleanField(
        default=True,
        help_text='Whether the user wants to receive SMS notifications.',
    )

    # ------------------------------------------------------------------ #
    # Manager & auth config
    # ------------------------------------------------------------------ #
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['role'], name='idx_user_role'),
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(
                fields=['is_active', 'role'],
                name='idx_user_active_role',
            ),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"

    # ------------------------------------------------------------------ #
    # Convenience properties
    # ------------------------------------------------------------------ #
    @property
    def full_name(self) -> str:
        """Return the user's full name, stripping extra whitespace."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_platform_admin(self) -> bool:
        """Check if user has the platform admin role."""
        return self.role == UserRole.PLATFORM_ADMIN

    @property
    def is_tenant_owner(self) -> bool:
        """Check if user has the tenant owner role."""
        return self.role == UserRole.TENANT_OWNER

    @property
    def is_tenant_manager(self) -> bool:
        """Check if user has the tenant manager role."""
        return self.role == UserRole.TENANT_MANAGER

    @property
    def is_customer(self) -> bool:
        """Check if user has the customer role."""
        return self.role == UserRole.CUSTOMER

    @property
    def is_vendor(self) -> bool:
        """Check if user has the vendor role."""
        return self.role == UserRole.VENDOR


class CustomerPreference(models.Model):
    """
    Stores customer preference weights for the recommendation engine.

    Each weight is an integer 0–100 indicating how important that factor
    is to the customer when searching for halls. The recommendation engine
    uses these weights to score and rank halls.

    Weight fields should ideally sum to 100 but this is not enforced at the
    model level — the recommendation engine normalizes them.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences',
        limit_choices_to={'role': UserRole.CUSTOMER},
    )

    # ------------------------------------------------------------------ #
    # Location preferences
    # ------------------------------------------------------------------ #
    preferred_city = models.CharField(max_length=100, blank=True, default='')
    preferred_state = models.CharField(max_length=100, blank=True, default='')

    # ------------------------------------------------------------------ #
    # Budget preferences
    # ------------------------------------------------------------------ #
    budget_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Minimum budget in INR.',
    )
    budget_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum budget in INR.',
    )

    # ------------------------------------------------------------------ #
    # Hall preferences
    # ------------------------------------------------------------------ #
    preferred_capacity = models.IntegerField(
        null=True,
        blank=True,
        help_text='Preferred guest capacity.',
    )
    preferred_hall_type = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Preferred hall type: indoor, outdoor, or both.',
    )

    # ------------------------------------------------------------------ #
    # Recommendation weights (0–100)
    # ------------------------------------------------------------------ #
    weight_budget = models.IntegerField(
        default=30,
        help_text='Importance of budget match (0-100).',
    )
    weight_capacity = models.IntegerField(
        default=20,
        help_text='Importance of capacity match (0-100).',
    )
    weight_proximity = models.IntegerField(
        default=20,
        help_text='Importance of geographic proximity (0-100).',
    )
    weight_amenities = models.IntegerField(
        default=15,
        help_text='Importance of amenity availability (0-100).',
    )
    weight_rating = models.IntegerField(
        default=15,
        help_text='Importance of hall rating (0-100).',
    )

    # ------------------------------------------------------------------ #
    # Timestamps
    # ------------------------------------------------------------------ #
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customer_preferences'
        verbose_name = 'Customer Preference'
        verbose_name_plural = 'Customer Preferences'

    def __str__(self) -> str:
        return f"Preferences for {self.user.email}"


class FavouriteHall(models.Model):
    """
    Customer's saved/favourite halls for quick access.

    Note: ``hall_id`` is stored as a raw UUIDField instead of a ForeignKey
    because the ``halls`` app has not been created yet (Phase 3). Once the
    Hall model exists, this field should be migrated to:
        hall = models.ForeignKey('halls.Hall', on_delete=models.CASCADE)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favourite_halls',
    )
    # TODO(Phase 3): Convert to ForeignKey('halls.Hall', on_delete=models.CASCADE)
    hall_id = models.UUIDField(
        help_text='UUID of the hall. Will become a FK to halls.Hall in Phase 3.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favourite_halls'
        verbose_name = 'Favourite Hall'
        verbose_name_plural = 'Favourite Halls'
        unique_together = ('user', 'hall_id')

    def __str__(self) -> str:
        return f"{self.user.email} → Hall {self.hall_id}"

