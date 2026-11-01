# HallBooking — Multi-Tenant Hall Booking SaaS

A platform where customers across India discover, compare and book community and event halls. Hall-owning businesses (tenants) subscribe to manage their locations, halls, managers and bookings.

| Layer | Stack |
|---|---|
| Backend | Python 3.12+, Django 5.1, Django REST Framework, SimpleJWT, PostgreSQL + PostGIS, Celery, Redis |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui-style components, TanStack Query |
| Integrations | Razorpay (subscriptions), S3-compatible storage, email (SMS planned) |

---

## 🚀 Run locally (macOS or Windows 11)

There are two ways to run the app:

- **Option A: Docker (recommended).** One command, identical on macOS and Windows 11, no Python/PostgreSQL/GDAL install.
- **Option B: Manual setup.** Run Django and Next.js directly on your machine. Best for day-to-day development with hot reload.

---

### Option A: Docker (one command) 🐳

**Prerequisite:** [Docker Desktop](https://www.docker.com/products/docker-desktop/). On Windows 11, use the default WSL2 backend. Docker Compose **v2.24+** is required; check with `docker compose version`.

From the **repository root**:

```bash
docker compose up --build
```

That's it. The same command works in macOS Terminal and Windows PowerShell. The first build takes a few minutes. When the logs settle, open:

| What | URL |
|---|---|
| **App (frontend)** | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/api/docs/ |
| Django admin | http://localhost:8000/admin/ |
| Health check | http://localhost:8000/api/health/ |

What happens on start:
1. PostGIS and Redis start.
2. The backend generates and applies database migrations, then serves the API with gunicorn.
3. The Celery worker and beat start once the backend is healthy.
4. The frontend starts.

**Create an admin user** in a second terminal, while the stack is running:

```bash
docker compose exec backend python manage.py createsuperuser
```

**Emails** (verification and password-reset links) are printed in the Celery worker logs:

```bash
docker compose logs -f celery_worker
```

**Everyday commands:**

| Task | Command |
|---|---|
| Start in background | `docker compose up -d --build` |
| Follow logs | `docker compose logs -f backend frontend` |
| Stop | `docker compose down` |
| Stop **and wipe the database** | `docker compose down -v` |
| Django shell | `docker compose exec backend python manage.py shell` |

**Optional configuration:** no `.env` file is needed. To change settings, copy `.env.example` to `.env` (`cp` on macOS, `Copy-Item` on Windows) and edit it. If ports 5432, 6379, 8000 or 3000 are already in use on your machine, set `DB_HOST_PORT`, `REDIS_HOST_PORT`, `BACKEND_HOST_PORT` or `FRONTEND_HOST_PORT` in `.env`.

> ⚠️ This stack uses Django **production settings** with HTTPS-only behaviour switched off so it works on `http://localhost`. Don't expose it publicly as-is. Put a TLS reverse proxy in front and remove the `DJANGO_SECURE_*=False` / `AUTH_COOKIE_SECURE=false` overrides in `docker/docker-compose.yml`.

---

### Option B: Manual setup (no Docker)

**Required versions:** Python **3.12 or 3.13** (64-bit), Node.js **20 or 22 LTS**, PostgreSQL **15–17** with **PostGIS 3.x**, and **GDAL** (needed by Django's geo features).

> Commands below are shown as **🍎 macOS (zsh/bash)** and **🪟 Windows 11 (PowerShell)**. Run everything from the **repository root** unless a step says otherwise.

#### Step 0. Install prerequisites (one time)

**🍎 macOS** (Homebrew):

```bash
brew install python@3.12 node@20 gdal postgis    # postgis installs a matching PostgreSQL
brew services start postgresql@17                 # use the version shown by `brew services list`
```

**🪟 Windows 11:**

1. **Python 3.12** from https://www.python.org/downloads/windows/ (tick *"Add python.exe to PATH"*).
2. **Node.js 20 LTS** from https://nodejs.org/.
3. **PostgreSQL 16** from https://www.enterprisedb.com/downloads/postgres-postgresql-downloads.
   - Remember the password you set for the `postgres` user.
   - At the end, let **Stack Builder** run and install *Spatial Extensions → PostGIS 3.x Bundle*.
   - Add `C:\Program Files\PostgreSQL\16\bin` to your PATH so `psql` works.
4. **GDAL** via OSGeo4W from https://trac.osgeo.org/osgeo4w/.
   - Choose *Express Install* and select **GDAL**; this installs to `C:\OSGeo4W`.
   - Find the exact DLL names. You'll need them in Step 2:
     ```powershell
     dir C:\OSGeo4W\bin\gdal*.dll
     dir C:\OSGeo4W\bin\geos_c.dll
     ```

> 🪟 **Easier on Windows:** use **Option A (Docker)**, or **WSL2 (Ubuntu)** with the Linux notes at the end of this section. Both avoid the GDAL/DLL setup.

#### Step 1. Create the database (one time)

The app expects user `hallbooking` / password `hallbooking` and database `hallbooking_db`. The user is created as a **superuser** so `migrate` can enable the PostGIS extension. That's fine for local development; never do it in production.

**🍎 macOS:**

```bash
psql postgres -c "CREATE ROLE hallbooking LOGIN SUPERUSER PASSWORD 'hallbooking';"
psql postgres -c "CREATE DATABASE hallbooking_db OWNER hallbooking;"
```

**🪟 Windows 11 (PowerShell):**

```powershell
psql -U postgres -c "CREATE ROLE hallbooking LOGIN SUPERUSER PASSWORD 'hallbooking';"
psql -U postgres -c "CREATE DATABASE hallbooking_db OWNER hallbooking;"
```

> **Alternative (any OS, if Docker Desktop works):** `docker compose up -d db` starts PostGIS on `localhost:5432` with these credentials, so you can skip Step 1. You still need GDAL installed locally for Django.

#### Step 2. Configure the environment (one time)

**🍎 macOS:**

```bash
cp .env.example .env
```

**🪟 Windows 11:**

```powershell
Copy-Item .env.example .env
```

Then open `.env`. The defaults work as-is, except for GDAL on these systems:

- **🪟 Windows (required):** Django 5.1 only auto-detects GDAL up to 3.8, and OSGeo4W ships newer versions. Uncomment and set both paths using the DLL names you found in Step 0. **Use forward slashes:**
  ```ini
  GDAL_LIBRARY_PATH=C:/OSGeo4W/bin/gdal310.dll
  GEOS_LIBRARY_PATH=C:/OSGeo4W/bin/geos_c.dll
  ```
- **🍎 macOS on Apple Silicon (only if you see "Could not find the GDAL library"):**
  ```ini
  GDAL_LIBRARY_PATH=/opt/homebrew/lib/libgdal.dylib
  GEOS_LIBRARY_PATH=/opt/homebrew/lib/libgeos_c.dylib
  ```

#### Step 3. Backend: Django API → http://localhost:8000

**🍎 macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/development.txt

cd backend
python manage.py makemigrations       # first run only: migration files aren't committed yet
python manage.py migrate
python manage.py createsuperuser      # becomes a platform_admin
python manage.py runserver 8000
```

**🪟 Windows 11 (PowerShell):**

```powershell
# If the repo already contains a "venv" folder created on macOS, delete it first:
#   Remove-Item -Recurse -Force venv
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1           # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements\development.txt

cd backend
python manage.py makemigrations       # first run only: migration files aren't committed yet
python manage.py migrate
python manage.py createsuperuser      # becomes a platform_admin
python manage.py runserver 8000
```

Check it is up:
- Health: http://localhost:8000/api/health/ → `{"status": "ok"}`
- Swagger UI: http://localhost:8000/api/docs/
- Django admin: http://localhost:8000/admin/

#### Step 4. Frontend: Next.js → http://localhost:3000

Open a **second terminal** at the repository root.

**🍎 macOS:**

```bash
cd frontend
cp .env.example .env.local            # API_BASE_URL=http://localhost:8000
npm install
npm run dev
```

**🪟 Windows 11 (PowerShell):**

```powershell
cd frontend
Copy-Item .env.example .env.local     # API_BASE_URL=http://localhost:8000
npm install
npm run dev
```

Open **http://localhost:3000**, click **Get started**, register, and you land on your dashboard.

#### Next time (daily start)

| | 🍎 macOS | 🪟 Windows 11 (PowerShell) |
|---|---|---|
| Terminal 1 | `source venv/bin/activate && cd backend && python manage.py runserver 8000` | `.\venv\Scripts\Activate.ps1; cd backend; python manage.py runserver 8000` |
| Terminal 2 | `cd frontend && npm run dev` | `cd frontend; npm run dev` |

Make sure PostgreSQL is running. On macOS use `brew services start postgresql@17`. On Windows the EDB installer runs it as a Windows service automatically.

#### What you do *not* need locally

- **Redis:** dev settings use an in-memory cache, and Celery runs tasks inline (eager mode). Set `DEV_USE_REDIS_CACHE=True` to use Redis. Celery workers don't run natively on Windows anyway; use Docker or WSL2 for them.
- **An email server:** emails (verification, password reset) are printed in the `runserver` terminal. Copy the link from there into the browser.
- **S3:** uploads go to `backend/media/` (`DEFAULT_FILE_STORAGE` in `.env`).
- **Razorpay keys:** billing isn't wired up yet (Phase 2 in progress).

#### Troubleshooting (manual setup)

| Symptom | Fix |
|---|---|
| `Could not find the GDAL library` | Set `GDAL_LIBRARY_PATH` / `GEOS_LIBRARY_PATH` in `.env` (Step 2). On Windows, point to the exact `gdalXXX.dll` in `C:/OSGeo4W/bin`. |
| `could not open extension control file ... postgis.control` | PostGIS isn't installed for the PostgreSQL version that's running. macOS: `brew install postgis` and run the matching `postgresql@N`. Windows: re-run Stack Builder → PostGIS bundle. |
| `permission denied to create extension "postgis"` | The `hallbooking` role isn't a superuser; re-run Step 1. |
| `connection refused` on port 5432 | PostgreSQL isn't running (see "Next time" above). |
| `Activate.ps1 cannot be loaded` (Windows) | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then reopen PowerShell. |
| Frontend shows "The server is unreachable" | The backend isn't running on :8000, or `API_BASE_URL` in `frontend/.env.local` is wrong. |
| Pages show "Coming soon" | Expected: those backend modules aren't built yet (see Project status). |

#### Linux / WSL2 (Ubuntu 22.04+)

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev gdal-bin libgdal-dev postgresql postgis
sudo service postgresql start
sudo -u postgres psql -c "CREATE ROLE hallbooking LOGIN SUPERUSER PASSWORD 'hallbooking';"
sudo -u postgres psql -c "CREATE DATABASE hallbooking_db OWNER hallbooking;"
# Node 20: https://github.com/nodesource/distributions  (or use nvm)
```

Then follow Steps 2–4 using the 🍎 macOS (bash) commands. GDAL is auto-detected on Linux, so leave the GDAL paths commented out.

### Useful commands

Commands are the same on macOS and Windows.

| Task | Command (from `backend/` with venv active, or `frontend/`) |
|---|---|
| Backend tests | `pytest` |
| Backend lint/format | `black . && isort . && flake8` |
| Frontend type-check | `npm run typecheck` |
| Frontend lint | `npm run lint` |
| Frontend production build | `npm run build && npm start` |
| Tests in Docker (PostGIS included) | `docker compose -f docker/docker-compose.test.yml run --rm tests` |
| Docker troubleshooting | `docker compose build --no-cache` to rebuild from scratch; `docker compose down -v` to reset data |

---

## 🧭 Project status

The build follows the phased plan in the architecture document.

| Phase | Scope | Status |
|---|---|---|
| 1 | `common`, `accounts`: settings, JWT auth, permissions, audit log, Docker | ✅ Done |
| 2 | `tenants`, `subscriptions`, `payments` (Razorpay) | 🟡 In progress: tenant models only, API not exposed yet |
| 3 | `locations`, `halls` | ⏳ |
| 4 | `discovery` (search + recommendation engine), `bookings`, `reviews` | ⏳ |
| 5 | `vendors`, `messaging`, `notifications` | ⏳ |
| 6 | Frontend | 🟡 Shell and account pages done; discovery, booking and compare pages built against the Phase 3–4 API contract |
| 7 | `analytics`, full test suite, CI/CD | ⏳ |

**Works end-to-end today:** register (customer/vendor), login/logout, email verification, forgot/reset password, profile, change password, customer recommendation preferences, and role-aware dashboards.

**Shows "Coming soon" until their backend phase lands:** hall search (`/halls`), hall detail and booking request, compare (`/compare`), and my bookings (`/bookings`).

**Known gaps:**
- No automated tests are written yet; `pytest` collects 0 tests.
- Migration files aren't committed yet. Docker generates them on start (`AUTO_MAKEMIGRATIONS=1`); the manual setup runs `makemigrations` once.

---

## 🏗️ Architecture

```
Browser ──▶ Next.js (:3000)
              ├─ pages (React, TanStack Query)
              └─ /api/auth/*, /api/proxy/*  ← BFF: JWTs live in httpOnly cookies
                        │  Bearer token (server-to-server)
                        ▼
            Django REST API (:8000, /api/v1/)
              ├─ TenantJWTAuthentication → request.tenant / request.tenant_membership
              ├─ RBAC + tenant-resource permissions, subscription write-guard
              ├─ service layer → PostgreSQL + PostGIS
              └─ Celery (Redis broker) → email, billing lifecycle jobs
```

Key decisions:
- **Multi-tenancy:** shared schema with a `tenant` foreign key on every tenant-owned table. `TenantMembership` (owner/manager) is the source of truth for tenant permissions. Public hall discovery uses separate, read-only querysets.
- **Auth:** email + password with JWT access (60 min) and refresh (7 days, rotated and blacklisted on logout). The browser never sees tokens; the Next.js server stores them in `httpOnly`, `SameSite=Lax` cookies.
- **Errors:** every API error has the shape `{"error": {"code", "message", "details"}}`.
- **Security:** auth endpoints are rate-limited per client IP. Email-verification tokens use a separate signer from password-reset tokens. Critical actions are written to the `AuditLog` table.

### API (live today)

All under `/api/v1/`. Full interactive docs at `/api/docs/`.

| Method | Endpoint | Auth |
|---|---|---|
| POST | `/auth/register/` | Public |
| POST | `/auth/login/` | Public |
| POST | `/auth/logout/` | Authenticated |
| POST | `/auth/token/refresh/` | Public (refresh token) |
| GET / PATCH | `/auth/me/` | Authenticated |
| POST | `/auth/change-password/` | Authenticated |
| POST | `/auth/password/reset/`, `/auth/password/reset/confirm/` | Public |
| POST | `/auth/verify-email/`, `/auth/verify-email/resend/` | Public / Authenticated |
| GET / PATCH | `/auth/preferences/` | Customer |

---

## 📁 Repository layout

```
.
├── backend/                 Django project
│   ├── config/              settings (base/development/production/test), urls, celery
│   └── apps/
│       ├── common/          base models, permissions, middleware, exceptions, audit log
│       ├── accounts/        custom User (email login, roles), auth APIs
│       └── tenants/         Tenant, TenantMembership, TenantInvitation (Phase 2, WIP)
├── frontend/                Next.js app (see frontend/README.md)
├── docker-compose.yml       `docker compose up --build` entry point (includes docker/docker-compose.yml)
├── docker/                  Dockerfile, docker-compose.yml, docker-compose.test.yml, entrypoint.sh
├── requirements/            base / development / production / test
└── .env.example             all configuration, with local-dev defaults
```

## ⚙️ Configuration

All backend settings come from environment variables in `.env` at the repo root (see `.env.example`). The ones that matter most:

| Variable | Default (dev) | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgis://hallbooking:hallbooking@localhost:5432/hallbooking_db` | PostGIS database |
| `DJANGO_SECRET_KEY` | insecure dev key | **Must** be set in production |
| `FRONTEND_URL` | `http://localhost:3000` | Base URL for links in emails |
| `DEFAULT_FILE_STORAGE` | `FileSystemStorage` | Use `storages.backends.s3boto3.S3Boto3Storage` + `AWS_*` for S3 |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache + Celery broker (production) |
| `RAZORPAY_*` | empty | Billing (Phase 2) |

The frontend needs only `API_BASE_URL` (in `frontend/.env.local`).
