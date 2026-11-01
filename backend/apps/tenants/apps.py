"""Django app configuration for tenant organisations."""
from django.apps import AppConfig


class TenantsConfig(AppConfig):
    """Tenants: organisations, memberships and manager invitations."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tenants'
    verbose_name = 'Tenants'
