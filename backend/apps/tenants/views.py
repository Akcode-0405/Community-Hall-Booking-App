"""
Views for the tenants app.
"""
from __future__ import annotations

from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsPlatformAdmin, IsTenantMember, IsTenantOwner
from .models import Tenant, TenantMembership, TenantStatus, SuspensionReason
from .serializers import TenantSerializer, TenantMembershipSerializer


class TenantListView(generics.ListCreateAPIView):
    """
    List tenants or create a new tenant.
    Platform admins see all tenants.
    Tenant owners see their own tenant(s).
    """
    serializer_class = TenantSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Tenant.objects.none()
        if getattr(user, 'role', None) == 'platform_admin':
            return Tenant.objects.all().order_by('name')
        # Return tenants where user is an active member
        return Tenant.objects.filter(memberships__user=user, memberships__is_active=True).distinct()

    def perform_create(self, serializer):
        tenant = serializer.save()
        # Add creating user as Tenant Owner
        TenantMembership.objects.create(
            user=self.request.user,
            tenant=tenant,
            role='owner',
            is_active=True,
        )
        # Update user's role if customer
        if self.request.user.role == 'customer':
            self.request.user.role = 'tenant_owner'
            self.request.user.save(update_fields=['role', 'updated_at'])


class TenantDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update tenant profile."""
    serializer_class = TenantSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Tenant.objects.none()
        if getattr(user, 'role', None) == 'platform_admin':
            return Tenant.objects.all()
        return Tenant.objects.filter(memberships__user=user, memberships__is_active=True).distinct()


class TenantSuspendView(APIView):
    """Platform admin can suspend a tenant account."""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def post(self, request: Request, id: str) -> Response:
        try:
            tenant = Tenant.objects.get(pk=id)
        except Tenant.DoesNotExist:
            return Response({'error': 'Tenant not found.'}, status=status.HTTP_404_NOT_FOUND)

        tenant.status = TenantStatus.SUSPENDED
        tenant.suspension_reason = SuspensionReason.ADMIN
        tenant.suspension_note = request.data.get('note', 'Suspended by platform administrator.')
        tenant.save(update_fields=['status', 'suspension_reason', 'suspension_note', 'updated_at'])
        return Response(TenantSerializer(tenant).data)


class TenantActivateView(APIView):
    """Platform admin can reactivate a suspended tenant account."""
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def post(self, request: Request, id: str) -> Response:
        try:
            tenant = Tenant.objects.get(pk=id)
        except Tenant.DoesNotExist:
            return Response({'error': 'Tenant not found.'}, status=status.HTTP_404_NOT_FOUND)

        tenant.status = TenantStatus.ACTIVE
        tenant.suspension_reason = SuspensionReason.NONE
        tenant.suspension_note = ''
        tenant.save(update_fields=['status', 'suspension_reason', 'suspension_note', 'updated_at'])
        return Response(TenantSerializer(tenant).data)


class CurrentTenantView(APIView):
    """Returns the primary tenant for the current authenticated owner/manager."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        membership = TenantMembership.objects.filter(
            user=request.user, is_active=True
        ).select_related('tenant').first()

        if not membership:
            return Response({'error': 'No active tenant found for this user.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'tenant': TenantSerializer(membership.tenant).data,
            'membership': TenantMembershipSerializer(membership).data,
        })

