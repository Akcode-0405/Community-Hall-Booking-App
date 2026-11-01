#!/bin/sh
# Container entrypoint.
#
# RUN_MIGRATIONS=1 (backend service only): apply database migrations before
# starting, so only one container ever migrates.
# AUTO_MAKEMIGRATIONS=1: generate migration files first. Temporary, until
# migration files are committed to the repository; generation is
# deterministic, so re-creating the container yields the same files.
set -e

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    if [ "${AUTO_MAKEMIGRATIONS:-0}" = "1" ]; then
        echo "Generating migration files..."
        python manage.py makemigrations --noinput
    fi
    echo "Applying database migrations..."
    python manage.py migrate --noinput
    echo "Seeding demo accounts and data..."
    python manage.py seed_demo_data || true
fi

exec "$@"
