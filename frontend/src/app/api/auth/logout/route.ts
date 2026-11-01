/** POST /api/auth/logout → blacklist the refresh token and clear cookies. */
import { NextRequest, NextResponse } from 'next/server';
import { ACCESS_COOKIE, API_PREFIX, REFRESH_COOKIE, clearAuthCookies } from '@/lib/server/backend';

export async function POST(req: NextRequest) {
  const access = req.cookies.get(ACCESS_COOKIE)?.value;
  const refresh = req.cookies.get(REFRESH_COOKIE)?.value;

  if (access && refresh) {
    // Best effort: even if blacklisting fails, the cookies are cleared.
    await fetch(`${API_PREFIX}/auth/logout/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${access}` },
      body: JSON.stringify({ refresh }),
      cache: 'no-store',
    }).catch(() => undefined);
  }

  const res = NextResponse.json({ detail: 'Logged out.' });
  clearAuthCookies(res);
  return res;
}
