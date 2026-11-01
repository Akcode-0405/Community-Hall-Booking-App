"""
Factory Boy factories for the accounts app testing.

Provides reusable factories for creating test instances of User,
CustomerPreference, and FavouriteHall models with sensible defaults.

Usage:
    from apps.accounts.tests.factories import UserFactory, CustomerFactory

    user = UserFactory()  # Creates a customer user
    admin = PlatformAdminFactory()  # Creates a platform admin
    vendor = VendorFactory(email='vendor@test.com')  # With custom email
"""
from __future__ import annotations

import uuid

import factory
from factory.django import DjangoModelFactory

from ..models import CustomerPreference, FavouriteHall, User, UserRole


class UserFactory(DjangoModelFactory):
    """
    Factory for creating User instances.

    Defaults to the 'customer' role with a unique email derived
    from the first and last name.
    """

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.LazyAttribute(
        lambda o: f"{o.first_name.lower()}.{o.last_name.lower()}@example.com"
    )
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = UserRole.CUSTOMER
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        raw_password = extracted if extracted is not None else 'testpass123'
        obj.set_password(raw_password)
        if create:
            obj.save(update_fields=['password'])


class PlatformAdminFactory(UserFactory):
    """Factory for creating platform admin users."""

    role = UserRole.PLATFORM_ADMIN
    is_staff = True
    is_superuser = True


class TenantOwnerFactory(UserFactory):
    """Factory for creating tenant owner users."""

    role = UserRole.TENANT_OWNER


class TenantManagerFactory(UserFactory):
    """Factory for creating tenant manager users."""

    role = UserRole.TENANT_MANAGER


class CustomerFactory(UserFactory):
    """Factory for creating customer users (same as default UserFactory)."""

    role = UserRole.CUSTOMER


class VendorFactory(UserFactory):
    """Factory for creating vendor users."""

    role = UserRole.VENDOR


class CustomerPreferenceFactory(DjangoModelFactory):
    """
    Factory for creating CustomerPreference instances.

    Note: Since a signal auto-creates preferences for customers,
    this factory is mainly useful when you need to customize preference
    values or create preferences for testing the recommendation engine.
    """

    class Meta:
        model = CustomerPreference

    user = factory.SubFactory(CustomerFactory)
    preferred_city = 'Bangalore'
    preferred_state = 'Karnataka'
    budget_min = 50000
    budget_max = 200000
    preferred_capacity = 200
    weight_budget = 30
    weight_capacity = 20
    weight_proximity = 20
    weight_amenities = 15
    weight_rating = 15


class FavouriteHallFactory(DjangoModelFactory):
    """Factory for creating FavouriteHall instances."""

    class Meta:
        model = FavouriteHall

    user = factory.SubFactory(CustomerFactory)
    hall_id = factory.LazyFunction(uuid.uuid4)

