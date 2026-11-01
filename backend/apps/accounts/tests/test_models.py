"""
Tests for apps.accounts models.
"""
from __future__ import annotations

import uuid

import pytest
from django.db import IntegrityError

from apps.accounts.models import CustomerPreference, FavouriteHall, User, UserRole
from apps.accounts.tests.factories import (
    CustomerFactory,
    PlatformAdminFactory,
    TenantManagerFactory,
    TenantOwnerFactory,
    UserFactory,
    VendorFactory,
)


@pytest.mark.django_db
class TestUserModel:
    """Test suite for custom User model and UserManager."""

    def test_create_user_with_email(self):
        """User can be created with email and password."""
        user = User.objects.create_user(
            email="test.user@example.com",
            password="securepassword123",
            first_name="Test",
            last_name="User",
        )
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email == "test.user@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.full_name == "Test User"
        assert user.check_password("securepassword123") is True
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.role == UserRole.CUSTOMER
        assert "Test User (test.user@example.com)" in str(user)

    def test_email_normalization(self):
        """Email domain is normalized to lowercase."""
        user = User.objects.create_user(
            email="TEST@EXAMPLE.COM",
            password="pass",
            first_name="A",
            last_name="B",
        )
        assert user.email == "TEST@example.com"

    def test_create_user_without_email_raises_error(self):
        """Creating user without email raises ValueError."""
        with pytest.raises(ValueError, match="Users must have an email address"):
            User.objects.create_user(email="", password="pass")

    def test_duplicate_email_raises_integrity_error(self):
        """Email must be unique."""
        UserFactory(email="unique@example.com")
        with pytest.raises(IntegrityError):
            UserFactory(email="unique@example.com")

    def test_create_superuser(self):
        """Superuser is created with staff and superuser permissions."""
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpassword123",
            first_name="Platform",
            last_name="Admin",
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == UserRole.PLATFORM_ADMIN
        assert admin.is_platform_admin is True

    def test_role_property_helpers(self):
        """Role boolean helper properties return correct values."""
        admin = PlatformAdminFactory()
        owner = TenantOwnerFactory()
        manager = TenantManagerFactory()
        customer = CustomerFactory()
        vendor = VendorFactory()

        assert admin.is_platform_admin is True
        assert admin.is_tenant_owner is False

        assert owner.is_tenant_owner is True
        assert owner.is_platform_admin is False

        assert manager.is_tenant_manager is True
        assert manager.is_tenant_owner is False

        assert customer.is_customer is True
        assert customer.is_vendor is False

        assert vendor.is_vendor is True
        assert vendor.is_customer is False


@pytest.mark.django_db
class TestCustomerPreferenceModel:
    """Test suite for CustomerPreference model."""

    def test_signal_auto_creates_preference_for_customer(self):
        """Post-save signal creates CustomerPreference when customer user is registered."""
        user = CustomerFactory()
        assert hasattr(user, "preferences")
        pref = user.preferences
        assert pref.weight_budget == 30
        assert pref.weight_capacity == 20
        assert pref.weight_proximity == 20
        assert pref.weight_amenities == 15
        assert pref.weight_rating == 15

    def test_signal_does_not_create_preference_for_vendor(self):
        """Preferences are not created for vendor or admin users."""
        vendor = VendorFactory()
        assert not hasattr(vendor, "preferences") or vendor.preferences is None


@pytest.mark.django_db
class TestFavouriteHallModel:
    """Test suite for FavouriteHall model."""

    def test_favourite_hall_creation_and_uniqueness(self):
        """Customer can save favourite halls, and duplicates are prevented."""
        customer = CustomerFactory()
        hall_uuid = uuid.uuid4()

        fav = FavouriteHall.objects.create(user=customer, hall_id=hall_uuid)
        assert fav.id is not None
        assert fav.user == customer
        assert fav.hall_id == hall_uuid

        # Duplicate should fail unique constraint
        with pytest.raises(IntegrityError):
            FavouriteHall.objects.create(user=customer, hall_id=hall_uuid)

