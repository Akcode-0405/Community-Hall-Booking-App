/**
 * Server-only helpers shared by the BFF route handlers.
 * Imported only from app/api/** route handlers and middleware.
 */
import type { NextResponse } from 'next/server';

export const BACKEND_URL = (process.env.API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');
export const API_PREFIX = `${BACKEND_URL}/api/v1`;

export const ACCESS_COOKIE = 'hb_access';
export const REFRESH_COOKIE = 'hb_refresh';

// Match SIMPLE_JWT lifetimes in backend/config/settings/base.py.
const ACCESS_MAX_AGE = 60 * 60; // 60 minutes
const REFRESH_MAX_AGE = 7 * 24 * 60 * 60; // 7 days

// Secure cookies in production unless AUTH_COOKIE_SECURE=false (local Docker
// over plain http://localhost, where Safari would otherwise drop them).
const secureCookies =
  process.env.AUTH_COOKIE_SECURE !== undefined
    ? process.env.AUTH_COOKIE_SECURE === 'true'
    : process.env.NODE_ENV === 'production';

const cookieBase = {
  httpOnly: true,
  secure: secureCookies,
  sameSite: 'lax' as const,
  path: '/',
};

export interface TokenPair {
  access: string;
  refresh?: string;
}

export function setAuthCookies(res: NextResponse, tokens: TokenPair) {
  res.cookies.set(ACCESS_COOKIE, tokens.access, { ...cookieBase, maxAge: ACCESS_MAX_AGE });
  if (tokens.refresh) {
    res.cookies.set(REFRESH_COOKIE, tokens.refresh, { ...cookieBase, maxAge: REFRESH_MAX_AGE });
  }
}

export function clearAuthCookies(res: NextResponse) {
  res.cookies.set(ACCESS_COOKIE, '', { ...cookieBase, maxAge: 0 });
  res.cookies.set(REFRESH_COOKIE, '', { ...cookieBase, maxAge: 0 });
}

/** Exchange a refresh token for a new pair (rotation is enabled server-side). */
export async function refreshTokens(refresh: string): Promise<TokenPair | null> {
  try {
    const res = await fetch(`${API_PREFIX}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
      cache: 'no-store',
    });
    if (!res.ok) return null;
    return (await res.json()) as TokenPair;
  } catch {
    return null;
  }
}

/**
 * Basic CSRF defence for cookie-authenticated mutations: if the browser
 * sends an Origin header it must match our own host.
 */
export function isSameOrigin(origin: string | null, host: string | null): boolean {
  if (!origin) return true;
  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}
