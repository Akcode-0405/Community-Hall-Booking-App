"""
Views for vendors, services, and customer bookings.
"""
from __future__ import annotations

from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import VendorCategory, VendorProfile, VendorService, VendorServiceBooking
from .serializers import (
    VendorCategorySerializer,
    VendorProfileSerializer,
    VendorServiceBookingSerializer,
    VendorServiceSerializer,
)


class PublicVendorListView(generics.ListAPIView):
    """Public listing of event vendors across India."""
    permission_classes = [permissions.AllowAny]
    serializer_class = VendorProfileSerializer

    def get_queryset(self):
        qs = VendorProfile.objects.filter(is_active=True).prefetch_related('services__category')
        city = self.request.query_params.get('city')
        if city:
            qs = qs.filter(city__iexact=city.strip())
        return qs


class PublicVendorDetailView(generics.RetrieveAPIView):
    """Public detail page for a single vendor with all their service packages."""
    permission_classes = [permissions.AllowAny]
    serializer_class = VendorProfileSerializer
    queryset = VendorProfile.objects.filter(is_active=True).prefetch_related('services__category')
    lookup_field = 'id'


class VendorCategoryListView(generics.ListAPIView):
    """List service categories (Catering, Decor, DJ, Photography)."""
    permission_classes = [permissions.AllowAny]
    serializer_class = VendorCategorySerializer
    queryset = VendorCategory.objects.all()
    pagination_class = None


class MyVendorProfileView(generics.RetrieveUpdateAPIView):
    """Vendor view to view and update their own business profile."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorProfileSerializer

    def get_object(self):
        profile, _ = VendorProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'business_name': f"{self.request.user.first_name}'s Services",
                'city': self.request.user.city or 'Bangalore',
                'state': self.request.user.state or 'Karnataka',
                'contact_email': self.request.user.email,
            },
        )
        return profile


class MyVendorServiceListCreateView(generics.ListCreateAPIView):
    """Vendor manages their own service packages."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorServiceSerializer

    def get_queryset(self):
        return VendorService.objects.filter(vendor__user=self.request.user).select_related('category')

    def perform_create(self, serializer):
        profile, _ = VendorProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'business_name': f"{self.request.user.first_name}'s Services",
                'city': self.request.user.city or 'Bangalore',
                'state': self.request.user.state or 'Karnataka',
                'contact_email': self.request.user.email,
            },
        )
        serializer.save(vendor=profile)


class MyVendorServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorServiceSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return VendorService.objects.filter(vendor__user=self.request.user)


class VendorBookingsView(generics.ListCreateAPIView):
    """
    List and submit customer service bookings.
    - Vendors see enquiries directed to their services.
    - Customers see enquiries they submitted to vendors.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorServiceBookingSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'vendor':
            return VendorServiceBooking.objects.filter(vendor_service__vendor__user=user).select_related(
                'vendor_service__vendor', 'customer'
            )
        return VendorServiceBooking.objects.filter(customer=user).select_related(
            'vendor_service__vendor', 'customer'
        )

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class VendorBookingRespondView(APIView):
    """Vendor updates status or quoted amount for an enquiry."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, id: str) -> Response:
        try:
            booking = VendorServiceBooking.objects.get(
                pk=id, vendor_service__vendor__user=request.user
            )
        except VendorServiceBooking.DoesNotExist:
            return Response({'error': 'Service booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        quoted_amount = request.data.get('quoted_amount')

        if new_status:
            booking.status = new_status
        if quoted_amount is not None:
            booking.quoted_amount = quoted_amount

        booking.save()
        return Response(VendorServiceBookingSerializer(booking).data)

