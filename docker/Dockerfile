# ==============================================================================
# Stage 1: Python base with system dependencies
# ==============================================================================
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies required for:
# - build-essential: compiling Python C extensions
# - libpq-dev: PostgreSQL client library (for psycopg)
# - gdal-bin, libgdal-dev: GDAL/OGR for PostGIS/GeoDjango support
# - libgeos-dev: Geometry Engine (used by PostGIS)
# - libproj-dev: Cartographic projection library (used by PostGIS)
# - gettext: Django translation tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        gettext \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# Stage 2: Install Python dependencies
# ==============================================================================
FROM base AS dependencies

WORKDIR /tmp

# Copy only requirements first to leverage Docker layer caching.
# Dependencies are only reinstalled when requirements files change.
# REQUIREMENTS selects the dependency set: production.txt (default) or test.txt
# for the CI / docker-compose.test.yml image.
ARG REQUIREMENTS=production.txt
COPY requirements/ /tmp/requirements/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements/${REQUIREMENTS}

# ==============================================================================
# Stage 3: Application
# ==============================================================================
FROM dependencies AS application

# Create a non-root user for security
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser

# Set the working directory
WORKDIR /app

# Copy application code and the container entrypoint
COPY backend/ /app/
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
# Strip Windows CRLF line endings (checkouts on Windows) so /bin/sh can run it.
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
    && chmod +x /usr/local/bin/entrypoint.sh

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# Collect static files at build time
RUN python manage.py collectstatic --noinput --settings=config.settings.production 2>/dev/null || true

# Health check — /api/health/ is exempt from the HTTPS redirect, so it can be
# probed over plain HTTP from inside the container.
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/')" || exit 1

ENTRYPOINT ["entrypoint.sh"]

# Default command: run gunicorn with production settings
CMD ["gunicorn", \
     "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
