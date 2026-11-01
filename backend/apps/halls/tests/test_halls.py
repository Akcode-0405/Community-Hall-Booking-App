"""
Tests for halls, discovery, comparison, and recommendation scoring.
"""
from __future__ import annotations

from decimal import Decimal
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.halls.models import Amenity, Hall, Location
from apps.halls.services import RecommendationEngine
from apps.tenants.models import Tenant, TenantMembership


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant_owner():
    return UserFactory(role='tenant_owner')


@pytest.fixture
def tenant(tenant_owner):
    t = Tenant.objects.create(
        name='Royal Palace Group',
        slug='royal-palace',
        contact_email='contact@royalpalace.com',
        city='Bangalore',
        state='Karnataka',
        pin_code='560001',
        status='active',
    )
    TenantMembership.objects.create(user=tenant_owner, tenant=t, role='owner', is_active=True)
    return t


@pytest.fixture
def location(tenant):
    return Location.objects.create(
        tenant=tenant,
        name='Koramangala Center',
        address_line_1='100 Feet Road, 4th Block',
        city='Bangalore',
        state='Karnataka',
        pin_code='560034',
        is_active=True,
    )


@pytest.fixture
def amenities():
    a1 = Amenity.objects.create(name='Central AC', category='comfort', icon='air-vent')
    a2 = Amenity.objects.create(name='Valet Parking', category='parking', icon='car')
    return [a1, a2]


@pytest.fixture
def sample_hall(tenant, location, amenities):
    hall = Hall.objects.create(
        tenant=tenant,
        location=location,
        name='Grand Peacock Ballroom',
        slug='grand-peacock-ballroom',
        description='Luxurious AC ballroom ideal for grand weddings.',
        capacity_min=100,
        capacity_max=1000,
        hall_type='indoor',
        base_price_per_day=Decimal('150000.00'),
        base_price_per_hour=Decimal('15000.00'),
        cleaning_fee=Decimal('5000.00'),
        security_deposit=Decimal('20000.00'),
        gst_percentage=Decimal('18.0'),
        avg_rating=Decimal('4.8'),
        review_count=24,
        is_active=True,
        is_published=True,
        photos=['https://images.unsplash.com/photo-1519167758481-83f550bb49b3?auto=format&fit=crop&w=1200&q=80'],
    )
    hall.amenities.set(amenities)
    return hall


@pytest.mark.django_db
class TestHallEndpoints:
    def test_public_hall_list(self, api_client, sample_hall):
        response = api_client.get('/api/v1/halls/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
        hall_data = results[0]
        assert hall_data['name'] == sample_hall.name
        assert hall_data['city'] == 'Bangalore'
        assert 'starting_price' in hall_data
        assert 'primary_photo_url' in hall_data
        assert isinstance(hall_data['amenities'], list)

    def test_public_hall_list_filter_city(self, api_client, sample_hall):
        res_match = api_client.get('/api/v1/halls/?city=Bangalore')
        assert len(res_match.data.get('results', res_match.data)) >= 1

        res_miss = api_client.get('/api/v1/halls/?city=Pune')
        assert len(res_miss.data.get('results', res_miss.data)) == 0

    def test_public_hall_detail(self, api_client, sample_hall):
        response = api_client.get(f'/api/v1/halls/{sample_hall.id}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data['id'] == str(sample_hall.id)
        assert data['name'] == sample_hall.name
        assert len(data['pricing']) >= 1
        assert len(data['taxes']) >= 1
        assert len(data['seating']) >= 1
        assert len(data['additional_charges']) >= 1

    def test_compare_halls(self, api_client, sample_hall, tenant, location):
        hall2 = Hall.objects.create(
            tenant=tenant,
            location=location,
            name='Lotus Lawn & Open Stage',
            slug='lotus-lawn',
            capacity_min=50,
            capacity_max=400,
            hall_type='outdoor',
            base_price_per_day=Decimal('75000.00'),
            is_active=True,
            is_published=True,
        )

        response = api_client.post('/api/v1/halls/compare/', {'hall_ids': [str(sample_hall.id), str(hall2.id)]}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'halls' in response.data
        assert len(response.data['halls']) == 2

    def test_tenant_create_hall(self, api_client, tenant_owner, location):
        api_client.force_authenticate(user=tenant_owner)
        payload = {
            'location': str(location.id),
            'name': 'Sapphire AC Hall',
            'description': 'Mid-size banquet space',
            'capacity_min': 50,
            'capacity_max': 300,
            'hall_type': 'indoor',
            'base_price_per_day': '50000.00',
            'base_price_per_hour': '5000.00',
            'cleaning_fee': '2500.00',
            'security_deposit': '10000.00',
            'gst_percentage': '18.0',
            'is_active': True,
            'is_published': True,
        }
        response = api_client.post('/api/v1/halls/manage/halls/', payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert Hall.objects.filter(name='Sapphire AC Hall').exists()

    def test_recommendation_engine_score(self, sample_hall):
        score_data = RecommendationEngine.calculate_hall_score(
            sample_hall,
            preferences=None,
            criteria={'budget_max': '200000'},
        )
        assert 0 <= score_data['match_score'] <= 100
        assert len(score_data['match_reasons']) > 0
        assert 'score_breakdown' in score_data
