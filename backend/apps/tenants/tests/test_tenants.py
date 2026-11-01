"""
Tests for tenant models and endpoints.
"""
from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.tenants.models import Tenant, TenantMembership, TenantStatus


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def platform_admin():
    return UserFactory(role='platform_admin')


@pytest.fixture
def tenant_owner():
    return UserFactory(role='tenant_owner')


@pytest.fixture
def customer():
    return UserFactory(role='customer')


@pytest.fixture
def sample_tenant(tenant_owner):
    tenant = Tenant.objects.create(
        name='Shree Grand Palace',
        slug='shree-grand-palace',
        contact_email='contact@shreegrand.com',
        city='Bangalore',
        state='Karnataka',
        pin_code='560001',
        status=TenantStatus.ACTIVE,
    )
    TenantMembership.objects.create(
        user=tenant_owner,
        tenant=tenant,
        role='owner',
        is_active=True,
    )
    return tenant


@pytest.mark.django_db
class TestTenantEndpoints:
    def test_list_tenants_as_platform_admin(self, api_client, platform_admin, sample_tenant):
        api_client.force_authenticate(user=platform_admin)
        response = api_client.get('/api/v1/tenants/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
        assert any(t['id'] == str(sample_tenant.id) for t in results)

    def test_list_tenants_as_tenant_owner_sees_only_own(self, api_client, tenant_owner, sample_tenant):
        # Create another tenant not belonging to tenant_owner
        other_owner = UserFactory(role='tenant_owner')
        other_tenant = Tenant.objects.create(
            name='Other Tenant Palace',
            slug='other-palace',
            contact_email='other@palace.com',
            city='Chennai',
            state='Tamil Nadu',
            pin_code='600001',
        )
        TenantMembership.objects.create(user=other_owner, tenant=other_tenant, role='owner', is_active=True)

        api_client.force_authenticate(user=tenant_owner)
        response = api_client.get('/api/v1/tenants/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 1
        assert results[0]['id'] == str(sample_tenant.id)

    def test_suspend_tenant_by_platform_admin(self, api_client, platform_admin, sample_tenant):
        api_client.force_authenticate(user=platform_admin)
        response = api_client.post(f'/api/v1/tenants/{sample_tenant.id}/suspend/', {'note': 'Policy violation'})
        assert response.status_code == status.HTTP_200_OK
        sample_tenant.refresh_from_db()
        assert sample_tenant.status == TenantStatus.SUSPENDED
        assert sample_tenant.suspension_note == 'Policy violation'

    def test_suspend_tenant_denied_for_regular_user(self, api_client, customer, sample_tenant):
        api_client.force_authenticate(user=customer)
        response = api_client.post(f'/api/v1/tenants/{sample_tenant.id}/suspend/', {'note': 'Test'})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_activate_tenant_by_platform_admin(self, api_client, platform_admin, sample_tenant):
        sample_tenant.status = TenantStatus.SUSPENDED
        sample_tenant.save()

        api_client.force_authenticate(user=platform_admin)
        response = api_client.post(f'/api/v1/tenants/{sample_tenant.id}/activate/')
        assert response.status_code == status.HTTP_200_OK
        sample_tenant.refresh_from_db()
        assert sample_tenant.status == TenantStatus.ACTIVE
