"""
Models for the complete booking lifecycle and audit history.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel, TenantAwareModel
from apps.common.utils import generate_booking_number
from apps.halls.models import Hall


class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Approval'
    CONFIRMED = 'confirmed', 'Confirmed'
    REJECTED = 'rejected', 'Rejected'
    CANCELLED = 'cancelled', 'Cancelled'
    COMPLETED = 'completed', 'Completed'


class EventType(models.TextChoices):
    WEDDING = 'wedding', 'Wedding'
    RECEPTION = 'reception', 'Reception'
    CONFERENCE = 'conference', 'Conference / Corporate'
    BIRTHDAY = 'birthday', 'Birthday Party'
    ANNIVERSARY = 'anniversary', 'Anniversary'
    EXHIBITION = 'exhibition', 'Exhibition / Trade Fair'
    OTHER = 'other', 'Other'


class SlotType(models.TextChoices):
    FULL_DAY = 'full_day', 'Full Day (9 AM - 10 PM)'
    HALF_DAY_MORNING = 'morning', 'Morning (8 AM - 2 PM)'
    HALF_DAY_EVENING = 'evening', 'Evening (4 PM - 11 PM)'
    HOURLY = 'hourly', 'Hourly Slot'


class Booking(TenantAwareModel):
    """
    Event hall booking record.
    Enforces multi-tenant data isolation and tracks complete financial breakdown.
    """
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    booking_number = models.CharField(max_length=32, unique=True, db_index=True)

    # Event details
    event_name = models.CharField(max_length=200)
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        default=EventType.WEDDING,
    )
    event_date = models.DateField(db_index=True)
    slot_type = models.CharField(
        max_length=30,
        choices=SlotType.choices,
        default=SlotType.FULL_DAY,
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    guest_count = models.PositiveIntegerField(default=100)
    special_requests = models.TextField(blank=True, default='')

    # Status
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        db_index=True,
    )

    # Financials (INR)
    base_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    additional_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Rejection & Cancellation
    rejection_reason = models.TextField(blank=True, default='')
    cancellation_reason = models.TextField(blank=True, default='')
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hall', 'event_date', 'status'], name='idx_booking_hall_date_stat'),
            models.Index(fields=['customer', 'status'], name='idx_booking_customer_stat'),
        ]

    def __str__(self) -> str:
        return f"{self.booking_number} ({self.hall.name} - {self.event_date})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.booking_number:
            self.booking_number = generate_booking_number()
        super().save(*args, **kwargs)


class BookingStatusLog(BaseModel):
    """Audit log of status changes for a booking."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_logs')
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'booking_status_logs'
        ordering = ['-created_at']
