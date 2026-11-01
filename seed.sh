#!/usr/bin/env bash
# ==============================================================================
# Script to seed demo data into the Hall Booking SaaS platform.
# Run this AFTER `docker compose up -d --build` finishes.
# ==============================================================================
set -e

echo "=========================================================="
echo "🌱 Seeding demo accounts and data for Hall Booking SaaS..."
echo "=========================================================="

if docker compose ps 2>/dev/null | grep -q "backend"; then
    echo "▶ Found running Docker backend container."
    echo "▶ Executing seeder inside container..."
    docker compose exec backend python manage.py seed_demo_data
elif [ -f "./venv/bin/python" ] && [ -f "backend/manage.py" ]; then
    echo "▶ Running seeder using local virtual environment..."
    ./venv/bin/python backend/manage.py seed_demo_data
elif [ -f "backend/manage.py" ]; then
    echo "▶ Running seeder using local Python..."
    python3 backend/manage.py seed_demo_data
else
    echo "❌ Error: Could not locate running Docker backend container or backend/manage.py."
    echo "Please ensure the app is running: docker compose up -d"
    exit 1
fi

echo "=========================================================="
echo "✅ Demo database seeding completed successfully!"
echo "=========================================================="
