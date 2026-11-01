"""
Models for locations, amenities, halls, availability, and reviews.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.common.models import BaseModel, TenantAwareModel
from apps.common.validators import PinCodeValidator


class Location(TenantAwareModel):
    """
    Physical venue location containing one or more halls.
    Belongs to a specific tenant.
    """
    name = models.CharField(max_length=200, help_text="Location name (e.g., Koramangala Hub)")
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    pin_code = models.CharField(max_length=6, validators=[PinCodeValidator()])
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'locations'
        ordering = ['city', 'name']

    def __str__(self) -> str:
        return f"{self.name} ({self.city})"


class Amenity(BaseModel):
    """Platform-wide amenity available to be assigned to halls."""
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True, default='check')
    category = models.CharField(max_length=50, blank=True, default='General')

    class Meta:
        db_table = 'amenities'
        verbose_name_plural = 'Amenities'
        ordering = ['category', 'name']

    def __str__(self) -> str:
        return self.name


class HallType(models.TextChoices):
    INDOOR = 'indoor', 'Indoor'
    OUTDOOR = 'outdoor', 'Outdoor'
    BOTH = 'both', 'Indoor & Outdoor'


class Hall(TenantAwareModel):
    """
    Individual event hall or banquet hall.
    Belongs to a tenant and is situated within a location.
    """
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='halls',
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True, default='')

    # Capacity
    capacity_min = models.PositiveIntegerField(default=50)
    capacity_max = models.PositiveIntegerField(default=500)

    # Classification
    hall_type = models.CharField(
        max_length=20,
        choices=HallType.choices,
        default=HallType.INDOOR,
    )

    # Visibility & Status
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True, db_index=True)

    # Ratings
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    review_count = models.PositiveIntegerField(default=0)

    # Amenities & Media
    amenities = models.ManyToManyField(Amenity, related_name='halls', blank=True)
    photos = models.JSONField(default=list, blank=True, help_text="List of photo URLs")

    # Pricing
    base_price_per_day = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50000.00'))
    base_price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('5000.00'))
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('2500.00'))
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10000.00'))
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'))

    # Policies
    cancellation_policy = models.TextField(
        default="Full refund up to 14 days before the event. 50% refund between 7-14 days. Non-refundable within 7 days."
    )

    class Meta:
        db_table = 'halls'
        ordering = ['-avg_rating', 'name']

    def __str__(self) -> str:
        return f"{self.name} - {self.location.city}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            base = slugify(self.name)[:180] or 'hall'
            self.slug = f"{base}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)


class HallAvailability(BaseModel):
    """Daily availability and schedule overrides for a hall."""
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='availability_calendar')
    date = models.DateField(db_index=True)
    is_available = models.BooleanField(default=True)
    reason = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        db_table = 'hall_availability'
        unique_together = ('hall', 'date')
        ordering = ['date']


class HallReview(BaseModel):
    """Customer ratings and feedback for a hall."""
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hall_reviews',
    )
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=150, blank=True, default='')
    comment = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'hall_reviews'
        ordering = ['-created_at']
