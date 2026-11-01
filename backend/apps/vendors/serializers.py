"""
Serializers for vendor profiles, services, and enquiries.
"""
from __future__ import annotations

from rest_framework import serializers

from apps.accounts.serializers import UserProfileSerializer
from .models import VendorCategory, VendorProfile, VendorService, VendorServiceBooking


class VendorCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorCategory
        fields = ['id', 'name', 'icon']


class VendorServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    vendor_business_name = serializers.ReadOnlyField(source='vendor.business_name')
    vendor_city = serializers.ReadOnlyField(source='vendor.city')
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2, source='price_from', required=False)

    class Meta:
        model = VendorService
        fields = [
            'id',
            'vendor',
            'vendor_business_name',
            'vendor_city',
            'category',
            'category_name',
            'title',
            'description',
            'price_from',
            'base_price',
            'price_to',
            'pricing_unit',
            'is_active',
        ]
        read_only_fields = ['id', 'vendor']


class VendorProfileSerializer(serializers.ModelSerializer):
    services = VendorServiceSerializer(many=True, read_only=True)
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id',
            'user',
            'business_name',
            'description',
            'city',
            'state',
            'contact_email',
            'contact_phone',
            'is_verified',
            'avg_rating',
            'review_count',
            'services',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class VendorServiceBookingSerializer(serializers.ModelSerializer):
    service_title = serializers.ReadOnlyField(source='vendor_service.title')
    vendor_business_name = serializers.ReadOnlyField(source='vendor_service.vendor.business_name')
    customer_name = serializers.ReadOnlyField(source='customer.full_name')
    customer_email = serializers.ReadOnlyField(source='customer.email')

    class Meta:
        model = VendorServiceBooking
        fields = [
            'id',
            'vendor_service',
            'service_title',
            'vendor_business_name',
            'customer_name',
            'customer_email',
            'event_date',
            'status',
            'quoted_amount',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
