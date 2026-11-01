"""
Serializers for booking management.
"""
from __future__ import annotations

from decimal import Decimal
from rest_framework import serializers

from apps.accounts.serializers import UserProfileSerializer
from apps.halls.models import Hall
from .models import Booking, BookingStatusLog


class BookingStatusLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.ReadOnlyField(source='changed_by.full_name')

    class Meta:
        model = BookingStatusLog
        fields = ['id', 'from_status', 'to_status', 'changed_by_name', 'notes', 'created_at']


class BookingListSerializer(serializers.ModelSerializer):
    hall = serializers.SerializerMethodField()
    hall_name = serializers.ReadOnlyField(source='hall.name')
    hall_city = serializers.ReadOnlyField(source='hall.location.city')
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    customer_name = serializers.ReadOnlyField(source='customer.full_name')
    customer_email = serializers.ReadOnlyField(source='customer.email')
    customer_phone = serializers.ReadOnlyField(source='customer.phone')
    primary_photo = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'booking_number',
            'hall',
            'hall_name',
            'hall_city',
            'tenant_name',
            'customer_name',
            'customer_email',
            'customer_phone',
            'primary_photo',
            'event_name',
            'event_type',
            'event_date',
            'slot_type',
            'start_time',
            'end_time',
            'guest_count',
            'status',
            'total_amount',
            'created_at',
        ]

    def get_hall(self, obj: Booking) -> dict:
        return {
            'id': str(obj.hall.id),
            'name': obj.hall.name,
            'city': obj.hall.location.city if obj.hall.location else '',
        }

    def get_start_time(self, obj: Booking) -> str:
        return str(obj.start_time) if obj.start_time else '10:00:00'

    def get_end_time(self, obj: Booking) -> str:
        return str(obj.end_time) if obj.end_time else '18:00:00'

    def get_primary_photo(self, obj: Booking) -> str | None:
        if obj.hall.photos and len(obj.hall.photos) > 0:
            p = obj.hall.photos[0]
            return p if isinstance(p, str) else p.get('url')
        return None


class BookingDetailSerializer(serializers.ModelSerializer):
    hall = serializers.SerializerMethodField()
    hall_name = serializers.ReadOnlyField(source='hall.name')
    hall_city = serializers.ReadOnlyField(source='hall.location.city')
    hall_address = serializers.ReadOnlyField(source='hall.location.address_line_1')
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    customer = UserProfileSerializer(read_only=True)
    status_logs = BookingStatusLogSerializer(many=True, read_only=True)
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'booking_number',
            'hall',
            'hall_name',
            'hall_city',
            'hall_address',
            'tenant',
            'tenant_name',
            'customer',
            'event_name',
            'event_type',
            'event_date',
            'slot_type',
            'start_time',
            'end_time',
            'guest_count',
            'special_requests',
            'status',
            'base_amount',
            'additional_charges',
            'tax_amount',
            'total_amount',
            'rejection_reason',
            'cancellation_reason',
            'confirmed_at',
            'cancelled_at',
            'status_logs',
            'created_at',
            'updated_at',
        ]

    def get_hall(self, obj: Booking) -> dict:
        return {
            'id': str(obj.hall.id),
            'name': obj.hall.name,
            'city': obj.hall.location.city if obj.hall.location else '',
        }

    def get_start_time(self, obj: Booking) -> str:
        return str(obj.start_time) if obj.start_time else '10:00:00'

    def get_end_time(self, obj: Booking) -> str:
        return str(obj.end_time) if obj.end_time else '18:00:00'


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer used by Customers to submit a booking request."""
    hall = serializers.PrimaryKeyRelatedField(
        queryset=Hall.objects.filter(is_active=True, is_published=True),
        required=True,
    )
    event_name = serializers.CharField(required=False, default='Special Event')
    event_type = serializers.CharField(required=False, default='wedding')
    slot_type = serializers.CharField(required=False, default='full_day')
    start_time = serializers.TimeField(required=False, default='10:00:00')
    end_time = serializers.TimeField(required=False, default='18:00:00')

    class Meta:
        model = Booking
        fields = [
            'id',
            'booking_number',
            'hall',
            'event_name',
            'event_type',
            'event_date',
            'slot_type',
            'start_time',
            'end_time',
            'guest_count',
            'special_requests',
            'status',
            'total_amount',
        ]
        read_only_fields = ['id', 'booking_number', 'status', 'total_amount']

    def validate(self, attrs):
        hall = attrs['hall']
        event_date = attrs['event_date']
        guest_count = attrs.get('guest_count', 100)

        # Capacity check
        if guest_count > hall.capacity_max:
            raise serializers.ValidationError({
                'guest_count': f"Guest count exceeds hall maximum capacity of {hall.capacity_max}."
            })

        # Check existing confirmed bookings on that date
        conflicts = Booking.objects.filter(
            hall=hall,
            event_date=event_date,
            status__in=['confirmed'],
        )
        if conflicts.exists():
            raise serializers.ValidationError({
                'event_date': "This hall is already booked and confirmed on this date. Please choose another date."
            })

        return attrs
