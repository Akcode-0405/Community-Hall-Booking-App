'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Badge, type BadgeProps } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { EmptyState, QueryError, Spinner } from '@/components/states';
import { useBookings, useCancelBooking } from '@/hooks/use-halls';
import { errorMessage } from '@/lib/api';
import type { Booking, BookingStatus } from '@/lib/types';
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
  { label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
];

function BookingRow({ booking }: { booking: Booking }) {
  const cancel = useCancelBooking();
  const cancellable = booking.status === 'pending' || booking.status === 'confirmed';

  return (
    <Card className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <Link href={`/halls/${booking.hall.id}`} className="font-semibold hover:underline">
            {booking.hall.name}
          </Link>
          <Badge variant={STATUS_VARIANT[booking.status]} className="capitalize">
            {booking.status}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {formatDate(booking.event_date)} · {formatTime(booking.start_time)}–{formatTime(booking.end_time)} · {booking.guest_count} guests ·{' '}
          {booking.hall.city}
        </p>
        <p className="text-xs text-muted-foreground">#{booking.booking_number}</p>
        {cancel.isError ? <p className="text-sm text-destructive">{errorMessage(cancel.error)}</p> : null}
      </div>
      <div className="flex items-center gap-4 sm:text-right">
        <span className="font-semibold">{formatINR(booking.total_amount)}</span>
        {cancellable ? (
          <Button
            variant="outline"
            size="sm"
            disabled={cancel.isPending}
            onClick={() => {
              const reason = window.prompt('Why are you cancelling? (shared with the hall)');
              if (reason !== null) cancel.mutate({ id: booking.id, reason });
            }}
          >
            {cancel.isPending ? 'Cancelling…' : 'Cancel'}
          </Button>
        ) : null}
      </div>
    </Card>
  );
}

export default function BookingsPage() {
  const [status, setStatus] = useState<BookingStatus | undefined>();
  const bookings = useBookings(status);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">My bookings</h1>

      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Filter by status">
        {TABS.map((t) => (
          <button
            key={t.label}
            role="tab"
            aria-selected={status === t.value}
            onClick={() => setStatus(t.value)}
            className={cn(
              'rounded-full border px-3 py-1 text-sm transition-colors',
              status === t.value ? 'border-primary bg-primary text-primary-foreground' : 'hover:bg-muted',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {bookings.isLoading ? (
        <Spinner />
      ) : bookings.isError ? (
        <QueryError error={bookings.error} />
      ) : !bookings.data?.results.length ? (
        <EmptyState
          title="No bookings yet"
          description="When you request a hall, it will appear here."
          action={
            <Button asChild>
              <Link href="/halls">Find a hall</Link>
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          {bookings.data.results.map((b) => (
            <BookingRow key={b.id} booking={b} />
          ))}
        </div>
      )}
    </div>
  );
}
