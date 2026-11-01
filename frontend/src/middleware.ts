/**
 * Route protection: signed-out users are redirected to /login for app pages.
 * This is a UX guard only — the Django API enforces all authorization.
 */
import { NextRequest, NextResponse } from 'next/server';

const PROTECTED = ['/dashboard', '/profile', '/preferences', '/bookings'];
const AUTH_PAGES = ['/login', '/register'];

export function middleware(req: NextRequest) {
  const { pathname, search } = req.nextUrl;
  const signedIn = Boolean(req.cookies.get('hb_refresh')?.value);

  if (!signedIn && PROTECTED.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    const url = req.nextUrl.clone();
    url.pathname = '/login';
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }

  if (signedIn && AUTH_PAGES.includes(pathname)) {
    const url = req.nextUrl.clone();
    url.pathname = '/dashboard';
    url.search = '';
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/profile/:path*', '/preferences/:path*', '/bookings/:path*', '/login', '/register'],
};
