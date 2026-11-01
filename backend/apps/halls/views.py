"""
Views for hall discovery, management, and comparison.
"""
from __future__ import annotations

from decimal import Decimal

from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsPlatformAdmin, IsTenantMember
from apps.tenants.models import TenantMembership
from .models import Amenity, Hall, HallAvailability, HallReview, Location
from .serializers import (
    AmenitySerializer,
    HallAvailabilitySerializer,
    HallCreateUpdateSerializer,
    HallDetailSerializer,
    HallListSerializer,
    LocationSerializer,
)
from .services import RecommendationEngine


class PublicHallListView(generics.ListAPIView):
    """
    Public discovery endpoint for searching & filtering halls across all active tenants.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = HallListSerializer

    def get_queryset(self):
        # Only show published halls from active tenants
        qs = Hall.objects.filter(
            is_active=True,
            is_published=True,
            tenant__status='active',
        ).select_related('location', 'tenant').prefetch_related('amenities')

        # Filters
        city = self.request.query_params.get('city')
        if city:
            qs = qs.filter(location__city__iexact=city.strip())

        state = self.request.query_params.get('state')
        if state:
            qs = qs.filter(location__state__iexact=state.strip())

        hall_type = self.request.query_params.get('hall_type')
        if hall_type and hall_type in ['indoor', 'outdoor', 'both']:
            qs = qs.filter(hall_type=hall_type)

        guests = self.request.query_params.get('guests')
        if guests and guests.isdigit():
            g = int(guests)
            qs = qs.filter(capacity_min__lte=g, capacity_max__gte=g)

        max_price = self.request.query_params.get('max_price')
        if max_price:
            try:
                qs = qs.filter(base_price_per_day__lte=Decimal(max_price))
            except Exception:
                pass

        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(location__name__icontains=q)
                | Q(location__city__icontains=q)
            )

        return qs


class PublicHallDetailView(generics.RetrieveAPIView):
    """Public detail page for a single hall."""
    permission_classes = [permissions.AllowAny]
    serializer_class = HallDetailSerializer
    queryset = Hall.objects.filter(is_active=True, is_published=True).select_related(
        'location', 'tenant'
    ).prefetch_related('amenities', 'reviews__customer')
    lookup_field = 'id'


class CompareHallsView(APIView):
    """
    Side-by-side comparison of 2 or more halls.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        hall_ids = request.data.get('hall_ids', [])
        if isinstance(hall_ids, str):
            hall_ids = [h.strip() for h in hall_ids.split(',') if h.strip()]
        elif not isinstance(hall_ids, list):
            hall_ids = list(request.data.getlist('hall_ids') if hasattr(request.data, 'getlist') else [])

        if not isinstance(hall_ids, list) or len(hall_ids) < 2:
            return Response(
                {'error': 'Provide at least two hall_ids in the list to compare.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        halls = Hall.objects.filter(id__in=hall_ids[:4]).select_related('location', 'tenant').prefetch_related('amenities')
        if len(halls) < 2:
            return Response({'error': 'Could not find at least two valid halls.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = HallDetailSerializer(halls, many=True, context={'request': request})
        return Response({'halls': serializer.data})


class AmenityListView(generics.ListAPIView):
    """Public listing of all amenities."""
    permission_classes = [permissions.AllowAny]
    serializer_class = AmenitySerializer
    queryset = Amenity.objects.all()
    pagination_class = None


# ---------------------------------------------------------------------------
# Tenant Manager / Owner Views
# ---------------------------------------------------------------------------


class LocationListCreateView(generics.ListCreateAPIView):
    """List or create locations for the active tenant."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LocationSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'platform_admin':
            return Location.objects.all().select_related('tenant')
        # Return locations for user's tenants
        return Location.objects.filter(tenant__memberships__user=user, tenant__memberships__is_active=True).distinct()

    def perform_create(self, serializer):
        # Resolve tenant from user's active membership
        membership = TenantMembership.objects.filter(user=self.request.user, is_active=True).first()
        if not membership:
            raise permissions.PermissionDenied("You are not associated with any active tenant organization.")
        serializer.save(tenant=membership.tenant)


class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LocationSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'platform_admin':
            return Location.objects.all()
        return Location.objects.filter(tenant__memberships__user=user, tenant__memberships__is_active=True).distinct()


class TenantHallListCreateView(generics.ListCreateAPIView):
    """
    Tenant Managers/Owners view all halls they own and add new halls.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return HallCreateUpdateSerializer
        return HallListSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'platform_admin':
            return Hall.objects.all().select_related('location', 'tenant').prefetch_related('amenities')
        return Hall.objects.filter(
            tenant__memberships__user=user, tenant__memberships__is_active=True
        ).select_related('location', 'tenant').prefetch_related('amenities').distinct()

    def perform_create(self, serializer):
        membership = TenantMembership.objects.filter(user=self.request.user, is_active=True).first()
        if not membership:
            raise permissions.PermissionDenied("No active tenant found.")
        serializer.save(tenant=membership.tenant)


class TenantHallDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = HallCreateUpdateSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'platform_admin':
            return Hall.objects.all()
        return Hall.objects.filter(tenant__memberships__user=user, tenant__memberships__is_active=True).distinct()


class HallAvailabilityView(APIView):
    """Get or update availability calendar for a hall."""
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request, hall_id: str) -> Response:
        availabilities = HallAvailability.objects.filter(hall_id=hall_id).order_by('date')
        serializer = HallAvailabilitySerializer(availabilities, many=True)
        return Response(serializer.data)

    def post(self, request: Request, hall_id: str) -> Response:
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        date = request.data.get('date')
        is_available = request.data.get('is_available', True)
        reason = request.data.get('reason', '')

        obj, _ = HallAvailability.objects.update_or_create(
            hall_id=hall_id,
            date=date,
            defaults={'is_available': is_available, 'reason': reason},
        )
        return Response(HallAvailabilitySerializer(obj).data)
