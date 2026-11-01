# HallBooking — Frontend

Next.js 14 (App Router) · TypeScript · Tailwind CSS · shadcn/ui-style components · TanStack Query.

## Run locally

Full macOS and Windows 11 instructions (including the backend) are in the [root README](../README.md#-run-locally-macos-or-windows-11). Frontend only:

```bash
# macOS / Linux
cp .env.example .env.local        # API_BASE_URL=http://localhost:8000
npm install
npm run dev                       # http://localhost:3000
```

```powershell
# Windows 11 (PowerShell)
Copy-Item .env.example .env.local
npm install
npm run dev
```

Checks: `npm run typecheck`, `npm run lint`, `npm run build`.

## How auth works (BFF pattern)

The browser never sees a JWT.

```
Browser ──/api/auth/login──▶ Next route handler ──▶ Django /api/v1/auth/login/
        ◀── {user} + httpOnly cookies (hb_access, hb_refresh)

Browser ──/api/proxy/<path>──▶ Next proxy ──Bearer <access>──▶ Django /api/v1/<path>/
                               (on 401: refresh once with hb_refresh, retry, rotate cookies)
```

- Cookies are `httpOnly`, `SameSite=Lax` and `Secure` in production. The proxy also rejects cross-origin mutations by checking the `Origin` header.
- `src/middleware.ts` redirects signed-out users away from app pages. This is only a UX guard; Django enforces every permission.
- Server-to-server calls mean no CORS setup is needed.

## Pages

| Route | Backend status |
|---|---|
| `/` landing + quick search | — |
| `/login`, `/register`, `/forgot-password` | ✅ live (`/auth/*`) |
| `/auth/reset-password`, `/auth/verify-email` (emailed links) | ✅ live |
| `/dashboard` (role-aware tiles) | ✅ live (tiles for unbuilt modules show "Coming soon") |
| `/profile` (profile + change password) | ✅ live |
| `/preferences` (recommendation weights) | ✅ live |
| `/halls`, `/halls/[id]`, `/compare` | ⏳ needs Phase 3–4 (`/discover/halls/`) |
| `/bookings`, booking request form | ⏳ needs Phase 4 (`/bookings/`) |

Pages for unbuilt endpoints show a "Coming soon" state, triggered when Django returns a non-JSON 404. They start working as soon as the backend serves the shapes defined in `src/lib/types.ts`, which is the contract for the Phase 3–4 serializers.

## Layout

```
src/
  app/
    (auth)/            login, register, forgot-password
    (app)/             signed-in pages: dashboard, profile, preferences, bookings
    auth/              emailed-link landing pages
    halls/, compare/   public discovery
    api/auth/*         BFF login/register/logout
    api/proxy/[...path] authenticated API proxy
  components/ui/       Button, Input, Card, Badge, Alert, Select, Textarea, Label
  hooks/               use-auth (account APIs), use-halls (discovery/bookings)
  lib/                 api client + ApiError, types, utils, server helpers
```
