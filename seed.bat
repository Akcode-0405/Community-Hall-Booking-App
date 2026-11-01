@echo off
REM ==============================================================================
REM Script to seed demo data into the Hall Booking SaaS platform on Windows.
REM Run this AFTER `docker compose up -d --build` finishes.
REM ==============================================================================
echo ==========================================================
echo Seeding demo accounts and data for Hall Booking SaaS...
echo ==========================================================

docker compose exec backend python manage.py seed_demo_data

echo ==========================================================
echo Demo database seeding completed successfully!
echo ==========================================================
