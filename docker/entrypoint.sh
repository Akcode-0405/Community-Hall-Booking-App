#!/bin/sh
# Container entrypoint.
#
# RUN_MIGRATIONS=1 (backend service only): apply database migrations before
# starting, so only one container ever migrates.
set -e

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    if [ "${AUTO_MAKEMIGRATIONS:-0}" = "1" ]; then
        echo "Generating migration files..."
        python manage.py makemigrations --noinput
    fi
    echo "Applying database migrations..."
    python manage.py migrate --noinput
fi

exec "$@"
