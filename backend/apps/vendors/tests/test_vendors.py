"""
Tests for vendor profile, service packages, and enquiry/quote workflows.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.vendors.models import VendorCategory, VendorProfile, VendorService, VendorServiceBooking


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def vendor_user():
    return UserFactory(role='vendor', email='vendor@tests.com')


@pytest.fixture
def customer_user():
    return UserFactory(role='customer', email='customer@tests.com')


@pytest.fixture
def vendor_category():
    return VendorCategory.objects.create(
        name='Floral & Theme Decor',
        icon='flower',
    )


@pytest.fixture
def vendor_profile(vendor_user):
    return VendorProfile.objects.create(
        user=vendor_user,
        business_name='Royal Floral Art',
        city='Bangalore',
        state='Karnataka',
        description='Specializing in royal mandap decor and stage lighting.',
        contact_email=vendor_user.email,
        is_active=True,
    )


@pytest.fixture
def vendor_service(vendor_profile, vendor_category):
    return VendorService.objects.create(
        vendor=vendor_profile,
        category=vendor_category,
        title='Luxury Crystal Mandap Decor',
        description='Imported fresh flowers with hanging chandeliers.',
        price_from=Decimal('75000.00'),
        pricing_unit='per_event',
        is_active=True,
    )


@pytest.mark.django_db
class TestVendorEndpoints:
    def test_get_and_patch_vendor_profile(self, api_client, vendor_user, vendor_profile):
        api_client.force_authenticate(user=vendor_user)
        response = api_client.get('/api/v1/vendors/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['business_name'] == 'Royal Floral Art'

        patch_res = api_client.patch('/api/v1/vendors/me/', {'city': 'Chennai'})
        assert patch_res.status_code == status.HTTP_200_OK
        vendor_profile.refresh_from_db()
        assert vendor_profile.city == 'Chennai'

    def test_create_vendor_service(self, api_client, vendor_user, vendor_profile, vendor_category):
        api_client.force_authenticate(user=vendor_user)
        payload = {
            'category': str(vendor_category.id),
            'title': 'Grand Entrance Arch',
            'description': 'Floral entrance arch with fairy lights',
            'price_from': '25000.00',
            'pricing_unit': 'per_event',
            'is_active': True,
        }
        response = api_client.post('/api/v1/vendors/services/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert VendorService.objects.filter(title='Grand Entrance Arch').exists()

    def test_customer_submits_vendor_enquiry(self, api_client, customer_user, vendor_service):
        api_client.force_authenticate(user=customer_user)
        payload = {
            'vendor_service': str(vendor_service.id),
            'event_date': str(date.today() + timedelta(days=25)),
            'notes': 'Looking for pastel pink and white color theme.',
        }
        response = api_client.post('/api/v1/vendors/bookings/', payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'enquiry'

    def test_vendor_provides_quotation(self, api_client, vendor_user, customer_user, vendor_service):
        enquiry = VendorServiceBooking.objects.create(
            vendor_service=vendor_service,
            customer=customer_user,
            event_date=date.today() + timedelta(days=25),
            notes='Need quotation for 2-day reception.',
            status='enquiry',
        )

        api_client.force_authenticate(user=vendor_user)
        response = api_client.post(f'/api/v1/vendors/bookings/{enquiry.id}/respond/', {
            'status': 'quoted',
            'quoted_amount': '85000.00',
        })
        assert response.status_code == status.HTTP_200_OK
        enquiry.refresh_from_db()
        assert enquiry.status == 'quoted'
        assert enquiry.quoted_amount == Decimal('85000.00')
