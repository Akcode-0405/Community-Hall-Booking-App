/**
 * Shared by the login and register BFF routes: forward credentials to
 * Django, keep the returned JWTs in httpOnly cookies, return only the user.
 */
import { NextRequest, NextResponse } from 'next/server';
import { setAuthCookies, type TokenPair } from './backend';

function clientIp(req: NextRequest): string | undefined {
  return req.headers.get('x-forwarded-for')?.split(',')[0].trim() || req.ip || undefined;
}

export async function authenticate(req: NextRequest, url: string) {
  let upstream: Response;
  try {
    upstream = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Django throttles auth endpoints per client IP; without this every
        // login would appear to come from the Next.js server.
        ...(clientIp(req) ? { 'X-Forwarded-For': clientIp(req) as string } : {}),
      },
      body: await req.text(),
      cache: 'no-store',
    });
  } catch {
    return NextResponse.json(
      { error: { code: 'BACKEND_UNAVAILABLE', message: 'The server is unreachable.', details: {} } },
      { status: 502 },
    );
  }

  const data = (await upstream.json().catch(() => ({}))) as { user?: unknown; tokens?: TokenPair };
  if (!upstream.ok || !data.tokens) {
    return NextResponse.json(data, { status: upstream.ok ? 500 : upstream.status });
  }

  // Only the user profile goes to the browser — never the tokens.
  const res = NextResponse.json({ user: data.user }, { status: upstream.status });
  setAuthCookies(res, data.tokens);
  return res;
}
