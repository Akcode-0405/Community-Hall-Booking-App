"""
Serializers for the tenants app.
"""
from __future__ import annotations

from rest_framework import serializers

from apps.accounts.serializers import UserProfileSerializer
from .models import Tenant, TenantMembership, TenantStatus


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for tenant organization details."""
    can_write = serializers.BooleanField(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'slug',
            'business_registration_number',
            'gstin',
            'contact_email',
            'contact_phone',
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'pin_code',
            'status',
            'suspension_reason',
            'can_write',
            'member_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'status', 'created_at', 'updated_at']

    def get_member_count(self, obj: Tenant) -> int:
        return obj.memberships.filter(is_active=True).count()


class TenantMembershipSerializer(serializers.ModelSerializer):
    """Serializer for tenant memberships."""
    user = UserProfileSerializer(read_only=True)
    tenant_name = serializers.ReadOnlyField(source='tenant.name')

    class Meta:
        model = TenantMembership
        fields = [
            'id',
            'user',
            'tenant',
            'tenant_name',
            'role',
            'is_active',
            'joined_at',
        ]
        read_only_fields = ['id', 'joined_at']
