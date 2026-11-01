"""
Signals for the accounts app.

Signal handlers:
- ``create_customer_preferences``: Automatically creates a CustomerPreference
  record when a new customer user is created. This ensures every customer
  has preferences initialized with sensible defaults for the recommendation
  engine.
"""
from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomerPreference, User, UserRole

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_customer_preferences(
    sender: type,
    instance: User,
    created: bool,
    **kwargs,
) -> None:
    """
    Create default CustomerPreference when a customer user is created.

    Uses get_or_create to be idempotent — safe to call multiple times
    (e.g., if the signal fires more than once due to test setup).

    Args:
        sender: The User model class.
        instance: The User instance that was saved.
        created: True if the instance was just created (INSERT).
        **kwargs: Additional signal keyword arguments.
    """
    if created and instance.role == UserRole.CUSTOMER:
        CustomerPreference.objects.get_or_create(user=instance)
        logger.debug(
            "Created default preferences for customer: %s",
            instance.email,
        )

