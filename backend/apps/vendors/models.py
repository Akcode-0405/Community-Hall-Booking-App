"""
Models for vendors, event service listings, and service enquiries.
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from apps.common.models import BaseModel


class VendorProfile(BaseModel):
    """Business profile for vendors (caterers, decorators, photographers, DJs)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_profile',
    )
    business_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    contact_email = models.EmailField()
    contact_phone = PhoneNumberField(blank=True, null=True, region='IN')
    is_verified = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('4.80'))
    review_count = models.PositiveIntegerField(default=12)

    class Meta:
        db_table = 'vendor_profiles'
        ordering = ['business_name']

    def __str__(self) -> str:
        return f"{self.business_name} ({self.city})"


class VendorCategory(BaseModel):
    """Category of event service (Catering, Decoration, Photography, etc.)."""
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True, default='star')

    class Meta:
        db_table = 'vendor_categories'
        verbose_name_plural = 'Vendor Categories'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class PricingUnit(models.TextChoices):
    PER_EVENT = 'per_event', 'Per Event'
    PER_PLATE = 'per_plate', 'Per Plate'
    PER_HOUR = 'per_hour', 'Per Hour'
    PER_DAY = 'per_day', 'Per Day'


class VendorService(BaseModel):
    """Individual service package offered by a vendor."""
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(VendorCategory, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    price_from = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('15000.00'))
    price_to = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pricing_unit = models.CharField(
        max_length=20,
        choices=PricingUnit.choices,
        default=PricingUnit.PER_EVENT,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'vendor_services'
        ordering = ['title']

    def __str__(self) -> str:
        return f"{self.title} - {self.vendor.business_name}"


class VendorServiceBooking(BaseModel):
    """Enquiry or confirmed booking of a vendor's service."""
    vendor_service = models.ForeignKey(VendorService, on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vendor_bookings')
    event_date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('enquiry', 'Enquiry / Pending'),
            ('confirmed', 'Confirmed'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='enquiry',
    )
    quoted_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'vendor_service_bookings'
        ordering = ['-created_at']

