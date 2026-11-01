/**
 * Authenticated API proxy: /api/proxy/<path> → Django /api/v1/<path>/
 *
 * - Reads the access token from an httpOnly cookie and sends it as a
 *   Bearer header (tokens never reach browser JavaScript).
 * - On 401, refreshes once using the refresh cookie and retries.
 * - Forwards X-Tenant-ID for multi-tenant staff users.
 */
import { NextRequest, NextResponse } from 'next/server';
import {
  ACCESS_COOKIE,
  API_PREFIX,
  REFRESH_COOKIE,
  clearAuthCookies,
  isSameOrigin,
  refreshTokens,
  setAuthCookies,
  type TokenPair,
} from '@/lib/server/backend';

export const dynamic = 'force-dynamic';

type Ctx = { params: { path: string[] } };

const FORWARDED_REQUEST_HEADERS = ['content-type', 'accept', 'x-tenant-id', 'accept-language'];

async function callBackend(
  req: NextRequest,
  url: string,
  body: ArrayBuffer | undefined,
  access: string | undefined,
): Promise<Response> {
  const headers = new Headers();
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = req.headers.get(name);
    if (value) headers.set(name, value);
  }
  if (access) headers.set('Authorization', `Bearer ${access}`);
  const forwardedFor = req.headers.get('x-forwarded-for') ?? req.ip;
  if (forwardedFor) headers.set('X-Forwarded-For', forwardedFor);

  return fetch(url, {
    method: req.method,
    headers,
    body: body && body.byteLength ? body : undefined,
    cache: 'no-store',
    redirect: 'manual',
  });
}

async function handler(req: NextRequest, { params }: Ctx) {
  if (req.method !== 'GET' && !isSameOrigin(req.headers.get('origin'), req.headers.get('host'))) {
    return NextResponse.json(
      { error: { code: 'FORBIDDEN', message: 'Cross-origin request rejected.', details: {} } },
      { status: 403 },
    );
  }

  // Django URLs end with a slash; keep query string as-is.
  const path = params.path.map(encodeURIComponent).join('/');
  const url = `${API_PREFIX}/${path}/${req.nextUrl.search}`;
  const body = ['GET', 'HEAD'].includes(req.method) ? undefined : await req.arrayBuffer();

  let access = req.cookies.get(ACCESS_COOKIE)?.value;
  const refresh = req.cookies.get(REFRESH_COOKIE)?.value;
  let refreshed: TokenPair | null = null;

  // Access cookie expired but refresh still valid → refresh up front.
  if (!access && refresh) {
    refreshed = await refreshTokens(refresh);
    access = refreshed?.access;
  }

  let upstream: Response;
  try {
    upstream = await callBackend(req, url, body, access);
    if (upstream.status === 401 && refresh && !refreshed) {
      refreshed = await refreshTokens(refresh);
      if (refreshed) upstream = await callBackend(req, url, body, refreshed.access);
    }
  } catch {
    return NextResponse.json(
      { error: { code: 'BACKEND_UNAVAILABLE', message: 'The server is unreachable. Please try again.', details: {} } },
      { status: 502 },
    );
  }

  const responseBody = upstream.status === 204 ? null : await upstream.arrayBuffer();
  const res = new NextResponse(responseBody, { status: upstream.status });
  const contentType = upstream.headers.get('content-type');
  if (contentType) res.headers.set('content-type', contentType);

  if (refreshed) setAuthCookies(res, refreshed);
  else if (upstream.status === 401 && refresh) clearAuthCookies(res);
  return res;
}

export { handler as GET, handler as POST, handler as PUT, handler as PATCH, handler as DELETE };
