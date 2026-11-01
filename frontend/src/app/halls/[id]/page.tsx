'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useState } from 'react';
import { CheckCircle2, MapPin, Star, Users } from 'lucide-react';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { FormField } from '@/components/form-field';
import { QueryError, Spinner } from '@/components/states';
import { useMe } from '@/hooks/use-auth';
import { useCreateBooking, useHall } from '@/hooks/use-halls';
import { ApiError, errorMessage } from '@/lib/api';
import type { HallDetail } from '@/lib/types';
import { formatINR } from '@/lib/utils';

const PRICING_LABELS: Record<string, string> = {
  hourly: 'Per hour',
  half_day: 'Half day',
  full_day: 'Full day',
  custom: 'Custom package',
};

function BookingForm({ hall }: { hall: HallDetail }) {
  const { data: user } = useMe();
  const create = useCreateBooking();
  const [form, setForm] = useState({ event_date: '', start_time: '10:00', end_time: '18:00', guest_count: '', special_requests: '' });
  const fieldErrors = create.error instanceof ApiError ? create.error.fieldErrors : {};
  const today = new Date().toISOString().slice(0, 10);

  if (!user) {
    return (
      <div className="space-y-3 text-sm">
        <p className="text-muted-foreground">Sign in as a customer to request this hall.</p>
        <Button asChild className="w-full">
          <Link href={`/login?next=/halls/${hall.id}`}>Sign in to book</Link>
        </Button>
      </div>
    );
  }
  if (user.role !== 'customer') {
    return <p className="text-sm text-muted-foreground">Only customer accounts can request bookings.</p>;
  }
  if (create.isSuccess) {
    return (
      <div className="space-y-3">
        <Alert variant="success">
          Request sent. Booking #{create.data.booking_number} is <strong>{create.data.status}</strong>; the hall manager will confirm it shortly.
        </Alert>
        <Button asChild variant="outline" className="w-full">
          <Link href="/bookings">View my bookings</Link>
        </Button>
      </div>
    );
  }

  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        create.mutate({
          hall: hall.id,
          event_date: form.event_date,
          start_time: form.start_time,
          end_time: form.end_time,
          guest_count: Number(form.guest_count),
          special_requests: form.special_requests || undefined,
        });
      }}
    >
      {create.isError ? (
        <Alert variant="destructive">
          {create.error instanceof ApiError && create.error.status === 409
            ? 'That slot was just booked by someone else. Please choose another time.'
            : errorMessage(create.error)}
        </Alert>
      ) : null}
      <FormField id="event_date" label="Event date" error={fieldErrors.event_date}>
        <Input type="date" min={today} required value={form.event_date} onChange={(e) => setForm({ ...form, event_date: e.target.value })} />
      </FormField>
      <div className="grid grid-cols-2 gap-3">
        <FormField id="start_time" label="From" error={fieldErrors.start_time}>
          <Input type="time" required value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
        </FormField>
        <FormField id="end_time" label="To" error={fieldErrors.end_time}>
          <Input type="time" required value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
        </FormField>
      </div>
      <FormField id="guest_count" label="Guests" error={fieldErrors.guest_count} hint={`This hall fits ${hall.capacity_min}–${hall.capacity_max} guests`}>
        <Input
          type="number"
          min={1}
          max={hall.capacity_max}
          required
          value={form.guest_count}
          onChange={(e) => setForm({ ...form, guest_count: e.target.value })}
        />
      </FormField>
      <FormField id="special_requests" label="Special requests (optional)">
        <Textarea value={form.special_requests} onChange={(e) => setForm({ ...form, special_requests: e.target.value })} />
      </FormField>
      <Button type="submit" className="w-full" disabled={create.isPending}>
        {create.isPending ? 'Sending request…' : 'Request booking'}
      </Button>
      <p className="text-xs text-muted-foreground">No payment now. The final price is confirmed by the hall.</p>
    </form>
  );
}

export default function HallDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: hall, isLoading, error } = useHall(id);

  if (isLoading) return <Spinner />;
  if (error || !hall) {
    return (
      <div className="container py-8">
        <QueryError error={error ?? new Error('Hall not found.')} />
      </div>
    );
  }

  const photos = hall.photos.length ? hall.photos : hall.primary_photo_url ? [{ id: 'primary', url: hall.primary_photo_url, caption: hall.name }] : [];

  return (
    <div className="container space-y-8 py-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">{hall.name}</h1>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <MapPin className="h-4 w-4" aria-hidden />
            {[hall.address_line_1, hall.locality, hall.city, hall.state, hall.pin_code].filter(Boolean).join(', ')}
          </span>
          <span className="flex items-center gap-1.5">
            <Users className="h-4 w-4" aria-hidden />
            {hall.capacity_min}–{hall.capacity_max} guests
          </span>
          <span className="flex items-center gap-1.5">
            <Star className="h-4 w-4" aria-hidden />
            {hall.avg_rating ? `${Number(hall.avg_rating).toFixed(1)} · ${hall.review_count} reviews` : 'No reviews yet'}
          </span>
          <Badge variant="outline" className="capitalize">
            {hall.hall_type}
          </Badge>
        </div>
      </div>

      {photos.length ? (
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {photos.slice(0, 6).map((p, i) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={p.id}
              src={p.url}
              alt={p.caption || hall.name}
              className={`aspect-[4/3] w-full rounded-lg object-cover ${i === 0 ? 'sm:col-span-2 sm:row-span-2 sm:aspect-auto sm:h-full' : ''}`}
            />
          ))}
        </div>
      ) : null}

      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <section>
            <h2 className="mb-2 text-lg font-semibold">About this hall</h2>
            <p className="whitespace-pre-line text-muted-foreground">{hall.description}</p>
          </section>

          {hall.amenities.length ? (
            <section>
              <h2 className="mb-3 text-lg font-semibold">Amenities</h2>
              <ul className="grid gap-2 sm:grid-cols-2">
                {hall.amenities.map((a) => (
                  <li key={a} className="flex items-center gap-2 text-sm">
                    <CheckCircle2 className="h-4 w-4 text-success" aria-hidden /> {a}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section>
            <h2 className="mb-3 text-lg font-semibold">Pricing</h2>
            <Card>
              <table className="w-full text-sm">
                <thead className="border-b text-left text-muted-foreground">
                  <tr>
                    <th className="p-3 font-medium">Package</th>
                    <th className="p-3 font-medium">Weekday</th>
                    <th className="p-3 font-medium">Weekend</th>
                  </tr>
                </thead>
                <tbody>
                  {hall.pricing.map((p) => (
                    <tr key={p.id} className="border-b last:border-0">
                      <td className="p-3">{PRICING_LABELS[p.pricing_type] ?? p.pricing_type}</td>
                      <td className="p-3 font-medium">{formatINR(p.base_price)}</td>
                      <td className="p-3">{formatINR(p.weekend_price ?? p.base_price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
            {hall.additional_charges.length || hall.taxes.length ? (
              <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
                {hall.additional_charges.map((c) => (
                  <li key={c.id}>
                    {c.name}: {c.charge_type === 'percentage' ? `${c.amount}%` : formatINR(c.amount)}
                    {c.is_mandatory ? ' (mandatory)' : ' (optional)'}
                  </li>
                ))}
                {hall.taxes.map((t) => (
                  <li key={t.tax_name}>
                    {t.tax_name}: {t.tax_percentage}% {t.is_inclusive ? '(included)' : '(extra)'}
                  </li>
                ))}
              </ul>
            ) : null}
          </section>

          {hall.seating.length ? (
            <section>
              <h2 className="mb-3 text-lg font-semibold">Seating layouts</h2>
              <div className="flex flex-wrap gap-2">
                {hall.seating.map((s) => (
                  <Badge key={s.arrangement_name} variant="secondary">
                    {s.arrangement_name}: {s.capacity}
                  </Badge>
                ))}
              </div>
            </section>
          ) : null}

          {hall.event_types.length ? (
            <section>
              <h2 className="mb-3 text-lg font-semibold">Suitable for</h2>
              <div className="flex flex-wrap gap-2">
                {hall.event_types.map((e) => (
                  <Badge key={e} variant="outline">
                    {e}
                  </Badge>
                ))}
              </div>
            </section>
          ) : null}

          <section>
            <h2 className="mb-2 text-lg font-semibold">Cancellation policy</h2>
            <p className="whitespace-pre-line text-sm text-muted-foreground">{hall.cancellation_policy || 'Contact the hall for details.'}</p>
          </section>
        </div>

        <aside className="lg:sticky lg:top-24 lg:self-start">
          <Card>
            <CardHeader>
              <CardTitle>
                From {formatINR(hall.starting_price)}
              </CardTitle>
              <CardDescription>Request a date; the hall confirms availability.</CardDescription>
            </CardHeader>
            <CardContent>
              <BookingForm hall={hall} />
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}
