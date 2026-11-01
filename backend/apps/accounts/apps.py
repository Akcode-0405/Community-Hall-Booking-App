"""
Django app configuration for the accounts module.

This app handles user management, authentication (JWT), registration,
profile management, and password management for the Hall Booking SaaS Platform.
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for the accounts Django application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'Accounts'

    def ready(self) -> None:
        """Import signal handlers when the app is ready."""
        import apps.accounts.signals  # noqa: F401

