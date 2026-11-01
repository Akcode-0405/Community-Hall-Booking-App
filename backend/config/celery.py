"""
Celery configuration for the Hall Booking SaaS Platform.

This module configures Celery for asynchronous task processing.
It uses Redis as the message broker and result backend.

Usage:
    Tasks are auto-discovered from all installed Django apps.
    Use @shared_task decorator in your apps' tasks.py files.
"""
import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
# This can be overridden by the DJANGO_SETTINGS_MODULE environment variable.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('hallbooking')

# Read config from Django settings, using the CELERY namespace.
# This means all celery-related configuration keys should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in all installed Django apps.
app.autodiscover_tasks()

# -----------------------------------------------------------------
# Default task configuration
# -----------------------------------------------------------------
app.conf.update(
    # Serialize task payloads as JSON for interoperability and security
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # Track when a task transitions to the STARTED state
    task_track_started=True,

    # Hard time limit: forcefully kill the task after 30 minutes
    task_time_limit=30 * 60,

    # Soft time limit: raise SoftTimeLimitExceeded after 25 minutes,
    # giving the task a chance to clean up gracefully
    task_soft_time_limit=25 * 60,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task that prints its own request info. Useful for testing Celery."""
    print(f'Request: {self.request!r}')
