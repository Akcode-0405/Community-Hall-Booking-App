'use client';

import Link from 'next/link';
import type { LucideIcon } from 'lucide-react';
import {
  BarChart3,
  Building2,
  CalendarDays,
  CreditCard,
  Heart,
  MessageSquare,
  Search,
  Settings2,
  ShieldCheck,
  Store,
  Users,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Spinner } from '@/components/states';
import { useMe } from '@/hooks/use-auth';
import type { UserRole } from '@/lib/types';
import { ROLE_LABELS } from '@/lib/utils';

interface Tile {
  title: string;
  body: string;
  icon: LucideIcon;
  href?: string;
  /** Set when the backend module isn't live yet. */
  soon?: boolean;
}

const TILES: Record<UserRole, Tile[]> = {
  customer: [
    { title: 'Find a hall', body: 'Search halls by city, date, guests and budget.', icon: Search, href: '/halls' },
    { title: 'My bookings', body: 'Track requests, confirmations and history.', icon: CalendarDays, href: '/bookings' },
    { title: 'Match preferences', body: 'Tune how halls are ranked for you.', icon: Settings2, href: '/preferences' },
    { title: 'Saved halls', body: 'Your shortlisted favourites.', icon: Heart, soon: true },
    { title: 'Conversations', body: 'Chat with hall managers and vendors.', icon: MessageSquare, soon: true },
  ],
  vendor: [
    { title: 'Vendor profile', body: 'Your business details and portfolio.', icon: Store, soon: true },
    { title: 'Service listings', body: 'Catering, décor, photography and more.', icon: Settings2, soon: true },
    { title: 'Enquiries & quotations', body: 'Respond to customers and share quotes.', icon: MessageSquare, soon: true },
    { title: 'Activity', body: 'Bookings and revenue statistics.', icon: BarChart3, soon: true },
  ],
  tenant_owner: [
    { title: 'Organisation', body: 'Business profile, GSTIN and contact details.', icon: Building2, soon: true },
    { title: 'Locations & halls', body: 'Halls, pricing, amenities and availability.', icon: Building2, soon: true },
    { title: 'Team', body: 'Invite managers and assign halls.', icon: Users, soon: true },
    { title: 'Bookings', body: 'Approve requests and manage the calendar.', icon: CalendarDays, soon: true },
    { title: 'Subscription & billing', body: 'Plan, invoices and payment history.', icon: CreditCard, soon: true },
    { title: 'Analytics', body: 'Revenue, utilisation and booking trends.', icon: BarChart3, soon: true },
  ],
  tenant_manager: [
    { title: 'My halls', body: 'Update details, pricing and availability.', icon: Building2, soon: true },
    { title: 'Bookings', body: 'Approve or reject requests for your halls.', icon: CalendarDays, soon: true },
    { title: 'Conversations', body: 'Reply to customer enquiries.', icon: MessageSquare, soon: true },
  ],
  platform_admin: [
    { title: 'Tenants', body: 'Approve, suspend and monitor tenants.', icon: ShieldCheck, soon: true },
    { title: 'Plans & subscriptions', body: 'Configure plans, track MRR and renewals.', icon: CreditCard, soon: true },
    { title: 'Platform analytics', body: 'Platform-wide bookings and revenue.', icon: BarChart3, soon: true },
  ],
};

export default function DashboardPage() {
  const { data: user, isLoading } = useMe();
  if (isLoading || !user) return <Spinner />;

  const tiles = TILES[user.role] ?? [];

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm text-muted-foreground">{ROLE_LABELS[user.role]}</p>
        <h1 className="text-2xl font-bold tracking-tight">Welcome, {user.first_name}</h1>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tiles.map(({ title, body, icon: Icon, href, soon }) => {
          const card = (
            <Card className={soon ? 'opacity-70' : 'h-full transition-colors hover:border-primary'}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Icon className="h-6 w-6 text-primary" aria-hidden />
                  {soon ? <Badge variant="secondary">Coming soon</Badge> : null}
                </div>
                <CardTitle className="pt-2 text-base">{title}</CardTitle>
                <CardDescription>{body}</CardDescription>
              </CardHeader>
            </Card>
          );
          return href && !soon ? (
            <Link key={title} href={href} className="block h-full">
              {card}
            </Link>
          ) : (
            <div key={title}>{card}</div>
          );
        })}
      </div>

      {user.role === 'platform_admin' ? (
        <p className="text-sm text-muted-foreground">
          Until the admin screens ship, use the{' '}
          <a href="http://localhost:8000/admin/" className="text-primary hover:underline">
            Django admin
          </a>{' '}
          and the{' '}
          <a href="http://localhost:8000/api/docs/" className="text-primary hover:underline">
            API docs
          </a>
          .
        </p>
      ) : null}
    </div>
  );
}
