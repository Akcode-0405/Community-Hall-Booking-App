/** POST /api/auth/register → Django register; logs the new user in. */
import { NextRequest } from 'next/server';
import { API_PREFIX } from '@/lib/server/backend';
import { authenticate } from '@/lib/server/authenticate';

export async function POST(req: NextRequest) {
  return authenticate(req, `${API_PREFIX}/auth/register/`);
}
