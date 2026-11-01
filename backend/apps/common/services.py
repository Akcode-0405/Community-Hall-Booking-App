"""
Base service layer for the Hall Booking SaaS Platform.

The service layer encapsulates business logic that doesn't belong in
models (which handle data integrity) or views/serializers (which handle
HTTP concerns).

All service classes should inherit from ``BaseService`` to ensure a
consistent pattern.  Services are the canonical place for:

    - Multi-model orchestration (e.g., creating a booking + payment)
    - External API calls (payment gateways, notification services)
    - Complex validation that spans multiple models
    - State machine transitions with side effects

Design principles:
    - Services are stateless — pass all required data as method arguments.
    - Services raise domain exceptions (from ``apps.common.exceptions``).
    - Services return model instances or simple data objects, never
      HTTP responses.
    - Database transactions are managed at the service level using
      ``django.db.transaction.atomic()``.

Example::

    class BookingService(BaseService):
        @staticmethod
        def create_booking(
            tenant: Tenant,
            hall: Hall,
            customer: User,
            start_time: datetime,
            end_time: datetime,
        ) -> Booking:
            with transaction.atomic():
                # Check for conflicts
                # Create booking
                # Create payment record
                # Send notifications
                ...
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class BaseService:
    """
    Base class for the service layer.

    All business logic services should inherit from this class.
    Provides common infrastructure such as logging setup.

    Subclasses should implement their domain methods as ``@staticmethod``
    or ``@classmethod`` methods — services are typically stateless.
    """

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """
        Return a logger namespaced to the concrete service class.

        Example::

            class BookingService(BaseService):
                def create(self, ...):
                    self.get_logger().info("Creating booking...")
        """
        return logging.getLogger(f"{cls.__module__}.{cls.__qualname__}")
