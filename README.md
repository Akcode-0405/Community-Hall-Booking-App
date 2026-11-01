# HallBooking — Multi-Tenant Hall Booking SaaS Platform

A production-ready, full-stack multi-tenant Hall Booking SaaS platform serving customers, banquet hall businesses (tenants), and event service vendors across India.

| Layer | Stack |
|---|---|
| Backend | Python 3.12+, Django 5.1, Django REST Framework, SimpleJWT, PostgreSQL + PostGIS, Celery, Redis |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui-style components, TanStack Query |
| Integrations | SaaS Multi-tenancy, Bayesian Recommendation Engine, Automated Seeding, REST API Proxy |

---

## 🚀 Run with Docker (Recommended)

### Step 1: Start the containers
Boots PostgreSQL PostGIS, Redis, Celery, Django REST API, and Next.js, and applies database schema migrations (does not seed data):

```bash
docker compose up -d --build
```

### Step 2: Seed Demo Data
After `docker compose up -d --build` finishes, run the seeder script to populate demo accounts, tenants, halls, bookings, and vendor services:

```bash
./seed.sh
```
*(On Windows: `seed.bat` or `docker compose exec backend python manage.py seed_demo_data`)*

When the services start, access the applications at:

| Component | URL | Notes |
|---|---|---|
| **Web Application** | [http://localhost:3000](http://localhost:3000) | Full Next.js frontend with all 4 user portals |
| **API Documentation** | [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) | Interactive Swagger UI for all REST endpoints |
| **Django Admin** | [http://localhost:8000/admin/](http://localhost:8000/admin/) | Platform backend administrative console |
| **Health Check** | [http://localhost:8000/api/health/](http://localhost:8000/api/health/) | Docker health probe |

---

## 👥 Demo Accounts (Pre-Seeded)

All 4 user roles are pre-configured with active data and ready for live presentation:

| Role | Email | Password | Pre-seeded Context / Organization |
| :--- | :--- | :--- | :--- |
| **Platform Admin** | `admin@hallbooking.com` | `AdminPass123!` | SaaS Owner: tenant oversight, suspension/reactivation, plans |
| **Tenant Manager** | `manager@grandpalace.com` | `ManagerPass123!` | *Grand Palace Conventions & Resorts* (Bangalore) |
| **Tenant Owner** | `owner@grandpalace.com` | `OwnerPass123!` | *Grand Palace Conventions & Resorts* (HQ) |
| **Customer** | `customer@example.com` | `CustomerPass123!` | Registered customer with preference weights and active bookings |
| **Vendor** | `vendor@royaldecor.com` | `VendorPass123!` | *Royal Décor & Catering Services* (Mandap, Catering, Photography) |

---

## 🎯 Step-by-Step Demo Guide for All 4 User Roles

### Role 1: Platform Admin (SaaS Owner)
1. Sign in at `http://localhost:3000/login` with `admin@hallbooking.com` / `AdminPass123!`.
2. Navigate to **Admin Portal** (`/admin-dashboard`).
3. View platform analytics: **Active Tenants**, **Suspended Accounts**, **Total Halls Live**, and **Monthly Recurring Revenue (MRR)**.
4. Manage Tenants: Click **[Suspend]** on any tenant account, enter a compliance reason, and watch the live badge flip to red **Suspended**. Click **[Reactivate]** to restore.
5. Review configured SaaS subscription tiers (*Starter*, *Professional*, *Enterprise*).

### Role 2: Tenant Manager / Owner (Venue Business)
1. Sign in with `manager@grandpalace.com` / `ManagerPass123!`.
2. Navigate to **Halls & Pricing** (`/tenant/halls`): Browse halls belonging to *Grand Palace Conventions* with pricing, capacities, and ratings.
3. Click **[+ Add New Hall]** to create and publish a new hall with custom pricing.
4. Navigate to **Bookings Queue** (`/tenant/bookings`): Filter by *Pending Approval*, inspect customer requests, and click **[Approve]** or **[Reject]**.
5. Navigate to **Locations** (`/tenant/locations`) to manage branch offices in Bangalore, Chennai, and Mumbai.

### Role 3: Customer (Event Planner)
1. Sign in with `customer@example.com` / `CustomerPass123!`.
2. Navigate to **Find halls** (`/halls`): Filter by city, guests, budget, and indoor/outdoor preference. Notice the recommendation engine match score percentage.
3. Open a hall detail page to view transparent pricing, taxes (18% GST), amenities, and seating options.
4. Compare halls side-by-side (`/compare`): Select two halls to compare starting prices, capacities, and amenities with highlighted advantages.
5. Submit a booking request for an upcoming date, then track and manage requests under **My bookings** (`/bookings`).
6. Customize weighting under **Preferences** (`/preferences`) to tune the recommendation engine.

### Role 4: Vendor (Event Services Partner)
1. Sign in with `vendor@royaldecor.com` / `VendorPass123!`.
2. Navigate to **My Services** (`/vendor/services`): View packages for floral decor, catering, and photography. Add new service packages.
3. Navigate to **Enquiries & Quotes** (`/vendor/bookings`): View customer enquiries, submit formal INR price quotes via **[Send Quote]**, and confirm bookings.
4. Navigate to **Business Profile** (`/vendor/profile`) to update verified business credentials, city, contact info, and portfolio bio.

---

## 🧪 Automated Testing & Verification

The test suite validates multi-tenant data isolation, atomic booking concurrency, scoring algorithms, and role permissions:

```bash
# Run backend test suite (118 tests)
pytest backend/ -c backend/pytest.ini

# Run frontend typecheck and production build
npm --prefix frontend run typecheck
npm --prefix frontend run lint
npm --prefix frontend run build
```

---

## 🏗️ Architecture & Security

- **Multi-Tenant Isolation**: Shared schema with tenant foreign keys and `TenantAwareModel` query filtering. Tenant operations verify active memberships.
- **Atomic Booking Concurrency**: PostgreSQL `select_for_update()` transaction locking prevents double-booking the same hall on the same date.
- **Secure Authentication**: Django REST Framework + SimpleJWT with access tokens stored strictly in secure `httpOnly` cookies via Next.js BFF proxy.
- **Bayesian Recommendation Engine**: 0–100 matching score combining budget fit, capacity, proximity, amenities, and Bayesian-damped customer ratings with full explainability breakdown.
