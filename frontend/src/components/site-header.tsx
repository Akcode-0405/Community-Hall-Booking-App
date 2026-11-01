'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { Building2, LogOut, Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLogout, useMe } from '@/hooks/use-auth';
import { cn, ROLE_LABELS } from '@/lib/utils';
import type { UserRole } from '@/lib/types';

interface NavItem {
  href: string;
  label: string;
  roles?: UserRole[];
}

const NAV: NavItem[] = [
  { href: '/halls', label: 'Find halls' },
  { href: '/compare', label: 'Compare', roles: ['customer'] },
  { href: '/dashboard', label: 'Dashboard', roles: ['customer', 'vendor', 'tenant_owner', 'tenant_manager', 'platform_admin'] },
  { href: '/bookings', label: 'My bookings', roles: ['customer'] },
  { href: '/preferences', label: 'Preferences', roles: ['customer'] },
];

export function SiteHeader() {
  const { data: user } = useMe();
  const logout = useLogout();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const items = NAV.filter((item) => !item.roles || (user && item.roles.includes(user.role)));

  const links = items.map((item) => (
    <Link
      key={item.href}
      href={item.href}
      onClick={() => setOpen(false)}
      className={cn(
        'rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground',
        pathname.startsWith(item.href) ? 'text-primary' : 'text-muted-foreground',
      )}
    >
      {item.label}
    </Link>
  ));

  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
      <div className="container flex h-16 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <Building2 className="h-6 w-6 text-primary" aria-hidden />
          <span>HallBooking</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
          {links}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          {user ? (
            <>
              <Link href="/profile" className="text-right text-sm leading-tight hover:underline">
                <span className="block font-medium">{user.full_name}</span>
                <span className="block text-xs text-muted-foreground">{ROLE_LABELS[user.role]}</span>
              </Link>
              <Button variant="ghost" size="icon" onClick={() => logout.mutate()} aria-label="Sign out">
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" asChild>
                <Link href="/login">Sign in</Link>
              </Button>
              <Button asChild>
                <Link href="/register">Get started</Link>
              </Button>
            </>
          )}
        </div>

        <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setOpen((o) => !o)} aria-label="Toggle menu" aria-expanded={open}>
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>

      {open ? (
        <nav className="container flex flex-col gap-1 border-t py-3 md:hidden" aria-label="Mobile">
          {links}
          {user ? (
            <>
              <Link href="/profile" onClick={() => setOpen(false)} className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent">
                Profile
              </Link>
              <button onClick={() => logout.mutate()} className="rounded-md px-3 py-2 text-left text-sm font-medium text-muted-foreground hover:bg-accent">
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" onClick={() => setOpen(false)} className="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent">
                Sign in
              </Link>
              <Link href="/register" onClick={() => setOpen(false)} className="rounded-md px-3 py-2 text-sm font-medium text-primary hover:bg-accent">
                Get started
              </Link>
            </>
          )}
        </nav>
      ) : null}
    </header>
  );
}
