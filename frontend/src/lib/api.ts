/**
 * Browser-side API client.
 *
 * All calls go to the Next.js proxy (/api/proxy/...), which attaches the
 * JWT from an httpOnly cookie and refreshes it transparently. The browser
 * never handles tokens directly.
 */
import type { ApiErrorBody } from './types';

export class ApiError extends Error {
  status: number;
  code: string;
  details: Record<string, unknown>;

  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }

  /** The endpoint doesn't exist yet (feature from a later backend phase). */
  get isNotImplemented(): boolean {
    return this.status === 404 && this.code === 'ENDPOINT_NOT_FOUND';
  }

  /** Map of field name → first error message, from DRF validation errors. */
  get fieldErrors(): Record<string, string> {
    const out: Record<string, string> = {};
    for (const [key, value] of Object.entries(this.details)) {
      if (key === 'non_field_errors' || key === 'errors') continue;
      if (Array.isArray(value) && value.length) out[key] = String(value[0]);
      else if (typeof value === 'string') out[key] = value;
    }
    return out;
  }
}

function isErrorBody(body: unknown): body is ApiErrorBody {
  return typeof body === 'object' && body !== null && 'error' in body;
}

async function parseError(res: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    // Non-JSON (e.g. Django's HTML 404 for an unknown URL)
  }
  if (isErrorBody(body)) {
    const { code, details } = body.error;
    const detailMap = (details ?? {}) as Record<string, unknown>;
    let { message } = body.error;
    if (code === 'VALIDATION_ERROR') {
      // Non-field errors (e.g. "Invalid email or password.") become the message;
      // otherwise point the user at the inline field errors.
      const nonField = detailMap.non_field_errors ?? (detailMap as { errors?: unknown }).errors;
      message = Array.isArray(nonField) && nonField.length ? String(nonField[0]) : 'Please correct the highlighted fields.';
    }
    return new ApiError(res.status, code, message, detailMap);
  }
  if (body && typeof body === 'object' && 'detail' in body) {
    return new ApiError(res.status, 'ERROR', String((body as { detail: unknown }).detail));
  }
  if (res.status === 404) {
    return new ApiError(404, 'NOT_FOUND', 'The requested resource was not found.');
  }
  return new ApiError(res.status, 'ERROR', `Request failed (${res.status}).`);
}

type Method = 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';

interface RequestOptions {
  method?: Method;
  body?: unknown;
  /** Query parameters; undefined/null/empty values are dropped. */
  params?: object;
  /** Override base (used for the /api/auth/* BFF routes). */
  base?: string;
}

export async function api<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, params, base = '/api/proxy' } = opts;
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries((params ?? {}) as Record<string, unknown>)) {
    if (v !== undefined && v !== null && v !== '') qs.set(k, String(v));
  }
  const url = `${base}${path}${qs.toString() ? `?${qs}` : ''}`;

  const res = await fetch(url, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'same-origin',
  });

  if (!res.ok) throw await parseError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return 'Something went wrong.';
}
