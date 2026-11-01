"""
Views for booking lifecycle: submit, approve, reject, cancel, and list.
"""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.exceptions import BookingConflictError
from .models import Booking, BookingStatus, BookingStatusLog
from .serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingListSerializer,
)


class BookingListCreateView(generics.ListCreateAPIView):
    """
    List bookings or create a new booking request.
    - Customers see their own bookings.
    - Tenant Managers/Owners see bookings for their tenant halls.
    - Platform Admins see all platform bookings.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BookingCreateSerializer
        return BookingListSerializer

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        if role == 'platform_admin':
            return Booking.objects.all().select_related('hall__location', 'tenant', 'customer')

        if role in ['tenant_owner', 'tenant_manager']:
            return Booking.objects.filter(
                tenant__memberships__user=user,
                tenant__memberships__is_active=True,
            ).select_related('hall__location', 'tenant', 'customer').distinct()

        # Customer sees their own
        return Booking.objects.filter(customer=user).select_related('hall__location', 'tenant', 'customer')

    @transaction.atomic
    def perform_create(self, serializer):
        customer = self.request.user
        hall = serializer.validated_data['hall']
        event_date = serializer.validated_data['event_date']

        # Concurrency safety: SELECT FOR UPDATE on existing bookings for this hall/date
        conflicts = Booking.objects.select_for_update().filter(
            hall=hall,
            event_date=event_date,
            status='confirmed',
        )
        if conflicts.exists():
            raise BookingConflictError(
                "A conflicting booking was just confirmed for this hall on this date."
            )

        # Automatic pricing calculation
        base_price = hall.base_price_per_day
        cleaning_fee = hall.cleaning_fee
        tax_amount = round((base_price + cleaning_fee) * (hall.gst_percentage / Decimal('100.0')), 2)
        total_amount = base_price + cleaning_fee + tax_amount

        booking = serializer.save(
            tenant=hall.tenant,
            customer=customer,
            status=BookingStatus.PENDING,
            base_amount=base_price,
            additional_charges=cleaning_fee,
            tax_amount=tax_amount,
            total_amount=total_amount,
        )

        BookingStatusLog.objects.create(
            booking=booking,
            from_status='',
            to_status=BookingStatus.PENDING,
            changed_by=customer,
            notes='Booking request submitted by customer.',
        )


class BookingDetailView(generics.RetrieveAPIView):
    """Retrieve booking details."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingDetailSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', None)

        if role == 'platform_admin':
            return Booking.objects.all().select_related('hall__location', 'tenant', 'customer')

        if role in ['tenant_owner', 'tenant_manager']:
            return Booking.objects.filter(
                tenant__memberships__user=user,
                tenant__memberships__is_active=True,
            ).select_related('hall__location', 'tenant', 'customer').distinct()

        return Booking.objects.filter(customer=user).select_related('hall__location', 'tenant', 'customer')


class BookingApproveView(APIView):
    """Tenant Manager / Owner approves a pending booking."""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request, id: str) -> Response:
        user = request.user
        try:
            booking = Booking.objects.select_for_update().get(pk=id)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Permission check: user must belong to tenant
        if user.role != 'platform_admin' and not booking.tenant.memberships.filter(user=user, is_active=True).exists():
            return Response({'error': 'You do not manage this hall.'}, status=status.HTTP_403_FORBIDDEN)

        if booking.status != BookingStatus.PENDING:
            return Response(
                {'error': f"Only pending bookings can be approved (current status: {booking.status})."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prev_status = booking.status
        booking.status = BookingStatus.CONFIRMED
        booking.confirmed_at = timezone.now()
        booking.save(update_fields=['status', 'confirmed_at', 'updated_at'])

        BookingStatusLog.objects.create(
            booking=booking,
            from_status=prev_status,
            to_status=BookingStatus.CONFIRMED,
            changed_by=user,
            notes=request.data.get('notes', 'Approved by hall management.'),
        )

        return Response(BookingDetailSerializer(booking).data)


class BookingRejectView(APIView):
    """Tenant Manager / Owner rejects a booking."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, id: str) -> Response:
        user = request.user
        try:
            booking = Booking.objects.get(pk=id)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user.role != 'platform_admin' and not booking.tenant.memberships.filter(user=user, is_active=True).exists():
            return Response({'error': 'You do not manage this hall.'}, status=status.HTTP_403_FORBIDDEN)

        reason = request.data.get('reason', 'Date unavailable or operational constraints.')
        prev_status = booking.status
        booking.status = BookingStatus.REJECTED
        booking.rejection_reason = reason
        booking.save(update_fields=['status', 'rejection_reason', 'updated_at'])

        BookingStatusLog.objects.create(
            booking=booking,
            from_status=prev_status,
            to_status=BookingStatus.REJECTED,
            changed_by=user,
            notes=f"Rejected: {reason}",
        )

        return Response(BookingDetailSerializer(booking).data)


class BookingCancelView(APIView):
    """Customer or Manager cancels a booking."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, id: str) -> Response:
        user = request.user
        try:
            booking = Booking.objects.get(pk=id)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Can be cancelled by customer or manager
        is_customer = (booking.customer == user)
        is_manager = (
            user.role == 'platform_admin'
            or booking.tenant.memberships.filter(user=user, is_active=True).exists()
        )

        if not (is_customer or is_manager):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        if booking.status in [BookingStatus.CANCELLED, BookingStatus.REJECTED]:
            return Response({'error': 'Booking is already cancelled or rejected.'}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason', 'Cancelled by user.')
        prev_status = booking.status
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = reason
        booking.cancelled_by = user
        booking.cancelled_at = timezone.now()
        booking.save(update_fields=['status', 'cancellation_reason', 'cancelled_by', 'cancelled_at', 'updated_at'])

        BookingStatusLog.objects.create(
            booking=booking,
            from_status=prev_status,
            to_status=BookingStatus.CANCELLED,
            changed_by=user,
            notes=f"Cancelled: {reason}",
        )

        return Response(BookingDetailSerializer(booking).data)

