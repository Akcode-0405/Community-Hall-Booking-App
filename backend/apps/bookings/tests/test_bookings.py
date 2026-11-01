"""
Tests for booking request lifecycle: create, conflict prevention, approve, reject, cancel.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.bookings.models import Booking, BookingStatus
from apps.halls.models import Hall, Location
from apps.tenants.models import Tenant, TenantMembership


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant_owner():
    return UserFactory(role='tenant_owner')


@pytest.fixture
def customer():
    return UserFactory(role='customer')


@pytest.fixture
def other_customer():
    return UserFactory(role='customer')


@pytest.fixture
def tenant(tenant_owner):
    t = Tenant.objects.create(
        name='Paradise Banquets',
        slug='paradise-banquets',
        city='Bangalore',
        state='Karnataka',
        status='active',
    )
    TenantMembership.objects.create(user=tenant_owner, tenant=t, role='owner', is_active=True)
    return t


@pytest.fixture
def location(tenant):
    return Location.objects.create(
        tenant=tenant,
        name='Main Branch',
        city='Bangalore',
        state='Karnataka',
        pin_code='560001',
    )


@pytest.fixture
def hall(tenant, location):
    return Hall.objects.create(
        tenant=tenant,
        location=location,
        name='Emerald Ballroom',
        slug='emerald-ballroom',
        capacity_min=50,
        capacity_max=500,
        hall_type='indoor',
        base_price_per_day=Decimal('100000.00'),
        cleaning_fee=Decimal('5000.00'),
        gst_percentage=Decimal('18.0'),
        is_active=True,
        is_published=True,
    )


@pytest.mark.django_db
class TestBookingLifecycle:
    def test_customer_creates_booking_request(self, api_client, customer, hall):
        api_client.force_authenticate(user=customer)
        event_date = str(date.today() + timedelta(days=30))
        payload = {
            'hall': str(hall.id),
            'event_date': event_date,
            'start_time': '10:00:00',
            'end_time': '18:00:00',
            'guest_count': 300,
            'special_requests': 'Require round table banquet layout.',
        }
        response = api_client.post('/api/v1/bookings/', payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == BookingStatus.PENDING
        assert Decimal(response.data['total_amount']) > Decimal('100000.00')

    def test_booking_guest_count_exceeds_capacity_rejected(self, api_client, customer, hall):
        api_client.force_authenticate(user=customer)
        event_date = str(date.today() + timedelta(days=20))
        payload = {
            'hall': str(hall.id),
            'event_date': event_date,
            'guest_count': 999,  # hall max is 500
        }
        response = api_client.post('/api/v1/bookings/', payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'guest_count' in str(response.data)

    def test_tenant_manager_approves_booking(self, api_client, tenant_owner, customer, hall, tenant):
        event_date = date.today() + timedelta(days=15)
        booking = Booking.objects.create(
            tenant=tenant,
            customer=customer,
            hall=hall,
            event_name='Grand Wedding',
            event_date=event_date,
            guest_count=250,
            base_amount=Decimal('100000.00'),
            total_amount=Decimal('123900.00'),
            status=BookingStatus.PENDING,
        )

        api_client.force_authenticate(user=tenant_owner)
        response = api_client.post(f'/api/v1/bookings/{booking.id}/approve/', {'notes': 'Deposit received, confirmed.'})
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.status == BookingStatus.CONFIRMED
        assert booking.status_logs.filter(to_status=BookingStatus.CONFIRMED).exists()

    def test_conflict_booking_rejected_when_already_confirmed(self, api_client, other_customer, customer, hall, tenant):
        event_date = date.today() + timedelta(days=40)
        # Existing confirmed booking
        Booking.objects.create(
            tenant=tenant,
            customer=customer,
            hall=hall,
            event_date=event_date,
            guest_count=200,
            base_amount=Decimal('100000.00'),
            total_amount=Decimal('123900.00'),
            status=BookingStatus.CONFIRMED,
        )

        api_client.force_authenticate(user=other_customer)
        payload = {
            'hall': str(hall.id),
            'event_date': str(event_date),
            'guest_count': 150,
        }
        response = api_client.post('/api/v1/bookings/', payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already booked' in str(response.data)

    def test_customer_cancels_booking(self, api_client, customer, hall, tenant):
        booking = Booking.objects.create(
            tenant=tenant,
            customer=customer,
            hall=hall,
            event_date=date.today() + timedelta(days=50),
            guest_count=100,
            base_amount=Decimal('100000.00'),
            total_amount=Decimal('123900.00'),
            status=BookingStatus.PENDING,
        )

        api_client.force_authenticate(user=customer)
        response = api_client.post(f'/api/v1/bookings/{booking.id}/cancel/', {'reason': 'Change of plans'})
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.status == BookingStatus.CANCELLED
        assert booking.cancellation_reason == 'Change of plans'
