'use client';

import Link from 'next/link';
import type { LucideIcon } from 'lucide-react';
import {
  BarChart3,
  Building2,
  CalendarDays,
  CreditCard,
  Heart,
  MapPin,
  MessageSquare,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Store,
  Users,
} from 'lucide-react';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Spinner } from '@/components/states';
import { useMe } from '@/hooks/use-auth';
import type { UserRole } from '@/lib/types';
import { ROLE_LABELS } from '@/lib/utils';

interface Tile {
  title: string;
  body: string;
  icon: LucideIcon;
  href: string;
}

const TILES: Record<UserRole, Tile[]> = {
  customer: [
    { title: 'Find a hall', body: 'Search halls by city, date, guests and budget.', icon: Search, href: '/halls' },
    { title: 'My bookings', body: 'Track requests, confirmations and history.', icon: CalendarDays, href: '/bookings' },
    { title: 'Match preferences', body: 'Tune how halls are ranked and scored for you.', icon: Settings2, href: '/preferences' },
    { title: 'Saved halls', body: 'Your shortlisted venues for comparison.', icon: Heart, href: '/saved-halls' },
    { title: 'Compare halls', body: 'Side-by-side venue differences & amenities.', icon: Sparkles, href: '/compare' },
  ],
  vendor: [
    { title: 'Vendor profile', body: 'Your verified business details, experience and bio.', icon: Store, href: '/vendor/profile' },
    { title: 'Service listings', body: 'Catering, floral decor, photography and packages.', icon: Sparkles, href: '/vendor/services' },
    { title: 'Enquiries & quotations', body: 'Respond to customers, send quotes and confirm.', icon: MessageSquare, href: '/vendor/bookings' },
    { title: 'Activity & bookings', body: 'Service bookings queue and client contacts.', icon: BarChart3, href: '/vendor/bookings' },
  ],
  tenant_owner: [
    { title: 'Locations & halls', body: 'Manage venues, daily pricing, amenities & capacity.', icon: Building2, href: '/tenant/halls' },
    { title: 'Bookings queue', body: 'Review customer booking requests, approve or reject.', icon: CalendarDays, href: '/tenant/bookings' },
    { title: 'Business locations', body: 'Manage branch offices and regional banquet centers.', icon: MapPin, href: '/tenant/locations' },
    { title: 'Subscription & billing', body: 'Plan tiers, hall limits and invoice history.', icon: CreditCard, href: '/admin-dashboard#plans' },
  ],
  tenant_manager: [
    { title: 'My halls', body: 'Update banquet details, pricing and availability.', icon: Building2, href: '/tenant/halls' },
    { title: 'Bookings queue', body: 'Approve or reject customer requests for your halls.', icon: CalendarDays, href: '/tenant/bookings' },
    { title: 'Locations', body: 'View assigned branches and hall allocations.', icon: MapPin, href: '/tenant/locations' },
  ],
  platform_admin: [
    { title: 'Tenant organizations', body: 'Manage tenants, review statuses, suspend or reactivate.', icon: ShieldCheck, href: '/admin-dashboard' },
    { title: 'Plans & subscriptions', body: 'Configure SaaS tiers, monitor MRR & platform revenue.', icon: CreditCard, href: '/admin-dashboard#plans' },
    { title: 'Platform analytics', body: 'Platform-wide halls, bookings, and active users.', icon: BarChart3, href: '/admin-dashboard' },
  ],
};

export default function DashboardPage() {
  const { data: user, isLoading } = useMe();
  if (isLoading || !user) return <Spinner />;

  const tiles = TILES[user.role] ?? [];

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-medium text-primary">{ROLE_LABELS[user.role]}</p>
        <h1 className="text-3xl font-bold tracking-tight">Welcome, {user.first_name}</h1>
        <p className="text-muted-foreground">Select an operational module below to manage your workflow.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tiles.map(({ title, body, icon: Icon, href }) => (
          <Link key={title} href={href} className="block h-full group">
            <Card className="h-full border transition-all duration-200 group-hover:border-primary group-hover:shadow-md">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="rounded-lg bg-primary/10 p-2 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <Icon className="h-6 w-6" aria-hidden />
                  </div>
                </div>
                <CardTitle className="pt-2 text-base group-hover:text-primary transition-colors">{title}</CardTitle>
                <CardDescription>{body}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>

      {user.role === 'platform_admin' ? (
        <div className="rounded-lg border bg-muted/40 p-4 text-sm text-muted-foreground flex flex-wrap items-center justify-between gap-3">
          <span>Platform administrator tooling is fully active.</span>
          <div className="flex gap-4">
            <a href="http://localhost:8000/admin/" target="_blank" rel="noreferrer" className="text-primary font-medium hover:underline">
              Open Django Admin →
            </a>
            <a href="http://localhost:8000/api/docs/" target="_blank" rel="noreferrer" className="text-primary font-medium hover:underline">
              Open Swagger API Docs →
            </a>
          </div>
        </div>
      ) : null}
    </div>
  );
}
