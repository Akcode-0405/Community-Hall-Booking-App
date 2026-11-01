"""
Django app configuration for the Common module.

The Common app provides shared base models, utilities, middleware,
permissions, exception handling, and pagination classes used by all
other apps in the Hall Booking SaaS Platform.
"""

from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
    verbose_name = "Common"
