'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  CalendarDays,
  CheckCircle2,
  DollarSign,
  Mail,
  MessageSquare,
  Phone,
  RefreshCw,
  Send,
  User,
} from 'lucide-react';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Spinner } from '@/components/states';
import { useRespondVendorBooking, useVendorBookings } from '@/hooks/use-vendor';
import { errorMessage } from '@/lib/api';
import { formatDate, formatINR } from '@/lib/utils';

export default function VendorBookingsPage() {
  const { data: bookingsData, isLoading, refetch, isFetching } = useVendorBookings();
  const respondBooking = useRespondVendorBooking();
  const [notice, setNotice] = useState<string | null>(null);

  if (isLoading) return <Spinner />;

  const bookings = bookingsData?.results ?? [];

  const handleQuote = async (id: string, serviceTitle: string) => {
    setNotice(null);
    const amountStr = window.prompt(`Enter quoted amount in INR (₹) for "${serviceTitle}":`, '65000');
    if (amountStr !== null && !isNaN(Number(amountStr))) {
      try {
        await respondBooking.mutateAsync({
          id,
          status: 'quoted',
          quoted_amount: amountStr,
        });
        setNotice(`Quotation of ₹${Number(amountStr).toLocaleString('en-IN')} sent to customer!`);
        refetch();
      } catch (err) {
        alert(`Failed to send quotation: ${errorMessage(err)}`);
      }
    }
  };

  const handleConfirm = async (id: string) => {
    setNotice(null);
    try {
      await respondBooking.mutateAsync({
        id,
        status: 'confirmed',
      });
      setNotice(`Service booking confirmed!`);
      refetch();
    } catch (err) {
      alert(`Failed to confirm: ${errorMessage(err)}`);
    }
  };

  return (
    <div className="space-y-6 py-2">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <MessageSquare className="h-7 w-7 text-primary" />
            <h1 className="text-3xl font-bold tracking-tight">Customer Enquiries & Quotations</h1>
          </div>
          <p className="text-muted-foreground">
            Respond to direct service inquiries, send formal price quotes, and manage bookings.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button asChild size="sm">
            <Link href="/vendor/services">Manage Services</Link>
          </Button>
        </div>
      </div>

      {notice ? (
        <Alert variant="success">
          <CheckCircle2 className="h-4 w-4" />
          {notice}
        </Alert>
      ) : null}

      {bookings.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground">
          No customer inquiries received yet.
        </Card>
      ) : (
        <div className="space-y-4">
          {bookings.map((b) => (
            <Card key={b.id} className="border">
              <CardContent className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-base font-bold">{b.service_title}</span>
                    <Badge
                      variant={
                        b.status === 'confirmed'
                          ? 'success'
                          : b.status === 'quoted'
                          ? 'default'
                          : 'secondary'
                      }
                      className="capitalize"
                    >
                      {b.status}
                    </Badge>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <CalendarDays className="h-4 w-4 text-primary" />
                      Event Date: {formatDate(b.event_date)}
                    </span>
                    <span className="flex items-center gap-1">
                      <User className="h-4 w-4" />
                      {b.customer_name}
                    </span>
                    {b.customer_email ? (
                      <span className="flex items-center gap-1">
                        <Mail className="h-3.5 w-3.5" />
                        {b.customer_email}
                      </span>
                    ) : null}
                  </div>

                  {b.notes ? (
                    <p className="rounded bg-muted/50 p-2 text-xs italic text-muted-foreground">
                      &quot;{b.notes}&quot;
                    </p>
                  ) : null}
                </div>

                <div className="flex flex-row items-center justify-between gap-4 border-t pt-3 lg:flex-col lg:items-end lg:border-t-0 lg:pt-0">
                  <div className="text-right">
                    <span className="text-xs text-muted-foreground">Quoted Price</span>
                    <div className="text-xl font-bold">
                      {b.quoted_amount ? formatINR(b.quoted_amount) : 'Not Quoted Yet'}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={respondBooking.isPending}
                      onClick={() => handleQuote(b.id, b.service_title)}
                    >
                      <Send className="mr-1 h-3.5 w-3.5" />
                      {b.quoted_amount ? 'Update Quote' : 'Send Quote'}
                    </Button>
                    {b.status !== 'confirmed' ? (
                      <Button
                        size="sm"
                        disabled={respondBooking.isPending}
                        onClick={() => handleConfirm(b.id)}
                      >
                        <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                        Confirm
                      </Button>
                    ) : null}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

