/** POST /api/auth/login → Django login; stores tokens in httpOnly cookies. */
import { NextRequest } from 'next/server';
import { API_PREFIX } from '@/lib/server/backend';
import { authenticate } from '@/lib/server/authenticate';

export async function POST(req: NextRequest) {
  return authenticate(req, `${API_PREFIX}/auth/login/`);
}
