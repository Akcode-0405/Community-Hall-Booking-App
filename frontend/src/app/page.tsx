'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { CalendarCheck, GitCompare, Search, ShieldCheck, Sparkles, Store } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

const FEATURES = [
  { icon: Search, title: 'Search across India', body: 'Filter by city, date, guests, budget, amenities and indoor/outdoor.' },
  { icon: Sparkles, title: 'Personalised matches', body: 'Every hall gets a 0–100 match score, with the reasons behind it.' },
  { icon: GitCompare, title: 'Side-by-side compare', body: 'Pricing, capacity, amenities and policies, with differences highlighted.' },
  { icon: CalendarCheck, title: 'Real-time availability', body: 'Request a slot, get approval from the hall manager and track status.' },
  { icon: Store, title: 'Event vendors', body: 'Caterers, decorators, photographers and DJs in one place.' },
  { icon: ShieldCheck, title: 'Built for hall owners', body: 'Manage locations, halls, pricing, managers and bookings in one dashboard.' },
];

export default function HomePage() {
  const router = useRouter();
  const [city, setCity] = useState('');
  const [date, setDate] = useState('');
  const [guests, setGuests] = useState('');

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    const qs = new URLSearchParams();
    if (city) qs.set('city', city);
    if (date) qs.set('event_date', date);
    if (guests) qs.set('guests', guests);
    router.push(`/halls?${qs}`);
  }

  return (
    <div>
      <section className="border-b bg-gradient-to-b from-accent/60 to-background">
        <div className="container py-16 md:py-24">
          <h1 className="max-w-3xl text-4xl font-bold tracking-tight md:text-5xl">
            The right hall for every celebration.
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
            Discover, compare and book wedding, party and community halls across India, from verified hall owners.
          </p>

          <form onSubmit={onSearch} className="mt-8 grid gap-3 rounded-xl border bg-card p-4 shadow-sm md:grid-cols-[2fr_1fr_1fr_auto]">
            <Input aria-label="City" placeholder="City, e.g. Bengaluru" value={city} onChange={(e) => setCity(e.target.value)} />
            <Input aria-label="Event date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            <Input aria-label="Guests" type="number" min={1} placeholder="Guests" value={guests} onChange={(e) => setGuests(e.target.value)} />
            <Button type="submit" size="lg">
              <Search className="h-4 w-4" aria-hidden /> Search
            </Button>
          </form>
        </div>
      </section>

      <section className="container py-16">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <Card key={title}>
              <CardHeader>
                <Icon className="h-6 w-6 text-primary" aria-hidden />
                <CardTitle className="pt-2 text-base">{title}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">{body}</CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="container pb-20">
        <Card className="flex flex-col items-start justify-between gap-4 p-8 md:flex-row md:items-center">
          <div>
            <h2 className="text-xl font-semibold">Own or manage event halls?</h2>
            <p className="mt-1 text-muted-foreground">List your halls, take bookings and manage your team on one platform.</p>
          </div>
          <Button asChild size="lg">
            <Link href="/register">Create an account</Link>
          </Button>
        </Card>
      </section>
    </div>
  );
}
