'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  CalendarDays,
  CheckCircle2,
  Clock,
  Mail,
  Phone,
  RefreshCw,
  User,
  XCircle,
} from 'lucide-react';
import { Alert } from '@/components/ui/alert';
import { Badge, type BadgeProps } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Spinner } from '@/components/states';
import { useBookings } from '@/hooks/use-halls';
import { useApproveBooking, useRejectBooking } from '@/hooks/use-tenant';
import { errorMessage } from '@/lib/api';
import type { BookingStatus } from '@/lib/types';
import { cn, formatDate, formatINR, formatTime } from '@/lib/utils';

const STATUS_VARIANT: Record<BookingStatus, BadgeProps['variant']> = {
  enquiry: 'outline',
  pending: 'secondary',
  confirmed: 'success',
  rejected: 'destructive',
  cancelled: 'outline',
  completed: 'default',
};

const TABS: { value?: BookingStatus; label: string }[] = [
  { label: 'All Requests' },
  { value: 'pending', label: 'Pending Approval' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'cancelled', label: 'Cancelled' },
];

export default function TenantBookingsPage() {
  const [selectedStatus, setSelectedStatus] = useState<BookingStatus | undefined>();
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const { data: bookingsData, isLoading, refetch, isFetching } = useBookings(selectedStatus);
  const approveBooking = useApproveBooking();
  const rejectBooking = useRejectBooking();

  if (isLoading) return <Spinner />;

  const bookings = bookingsData?.results ?? [];

  const handleApprove = async (id: string, bookingNumber: string) => {
    setActionNotice(null);
    try {
      await approveBooking.mutateAsync({ id, notes: 'Approved by Hall Management' });
      setActionNotice(`Booking #${bookingNumber} was approved and confirmed!`);
      refetch();
    } catch (err) {
      alert(`Approval failed: ${errorMessage(err)}`);
    }
  };

  const handleReject = async (id: string, bookingNumber: string) => {
    setActionNotice(null);
    const reason = window.prompt('Please enter reason for rejecting this booking:', 'Hall under scheduled maintenance');
    if (reason !== null) {
      try {
        await rejectBooking.mutateAsync({ id, reason });
        setActionNotice(`Booking #${bookingNumber} was rejected.`);
        refetch();
      } catch (err) {
        alert(`Rejection failed: ${errorMessage(err)}`);
      }
    }
  };

  return (
    <div className="space-y-6 py-2">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <CalendarDays className="h-7 w-7 text-primary" />
            <h1 className="text-3xl font-bold tracking-tight">Bookings & Reservations</h1>
          </div>
          <p className="text-muted-foreground">
            Review customer reservation requests, approve dates, or resolve conflicts.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button asChild size="sm">
            <Link href="/tenant/halls">Manage Halls</Link>
          </Button>
        </div>
      </div>

      {actionNotice ? (
        <Alert variant="success">
          <CheckCircle2 className="h-4 w-4" />
          {actionNotice}
        </Alert>
      ) : null}

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b pb-3">
        {TABS.map((t) => (
          <button
            key={t.label}
            onClick={() => setSelectedStatus(t.value)}
            className={cn(
              'rounded-full px-4 py-1.5 text-sm font-medium transition-colors',
              selectedStatus === t.value
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted/80',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Bookings Queue */}
      {bookings.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground">
          No bookings found matching this filter.
        </Card>
      ) : (
        <div className="space-y-4">
          {bookings.map((b) => (
            <Card key={b.id} className="overflow-hidden border">
              <div className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-lg font-bold">
                      {b.hall.name}
                    </span>
                    <Badge variant={STATUS_VARIANT[b.status]} className="capitalize">
                      {b.status}
                    </Badge>
                    <span className="text-xs text-muted-foreground">#{b.booking_number}</span>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <CalendarDays className="h-4 w-4 text-primary" />
                      {formatDate(b.event_date)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-4 w-4 text-primary" />
                      {formatTime(b.start_time)} – {formatTime(b.end_time)}
                    </span>
                    <span>{b.guest_count} Expected Guests</span>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <User className="h-3.5 w-3.5" />
                      Customer: {(b as any).customer_name || 'Registered Customer'}
                    </span>
                    {(b as any).customer_email ? (
                      <span className="flex items-center gap-1">
                        <Mail className="h-3.5 w-3.5" />
                        {(b as any).customer_email}
                      </span>
                    ) : null}
                    {(b as any).customer_phone ? (
                      <span className="flex items-center gap-1">
                        <Phone className="h-3.5 w-3.5" />
                        {(b as any).customer_phone}
                      </span>
                    ) : null}
                  </div>
                </div>

                <div className="flex flex-row items-center justify-between gap-4 border-t pt-3 lg:flex-col lg:items-end lg:border-t-0 lg:pt-0">
                  <div className="text-right">
                    <span className="text-xs text-muted-foreground">Total (incl. 18% GST)</span>
                    <div className="text-xl font-bold">{formatINR(b.total_amount)}</div>
                  </div>

                  {b.status === 'pending' ? (
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        disabled={approveBooking.isPending}
                        onClick={() => handleApprove(b.id, b.booking_number)}
                      >
                        <CheckCircle2 className="mr-1 h-4 w-4 text-white" />
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        disabled={rejectBooking.isPending}
                        onClick={() => handleReject(b.id, b.booking_number)}
                      >
                        <XCircle className="mr-1 h-4 w-4" />
                        Reject
                      </Button>
                    </div>
                  ) : null}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
