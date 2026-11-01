"""
Django admin configuration for the accounts app.

Registers User, CustomerPreference, and FavouriteHall models with the
Django admin site, with customized list displays, filters, and fieldsets.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CustomerPreference, FavouriteHall, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom User model.

    Extends Django's built-in UserAdmin with:
    - Email-based authentication fields (no username).
    - Role and verification status filters.
    - Custom fieldsets for the platform's user fields.
    """

    list_display = (
        'email',
        'first_name',
        'last_name',
        'role',
        'is_active',
        'is_email_verified',
        'date_joined',
    )
    list_filter = (
        'role',
        'is_active',
        'is_staff',
        'is_email_verified',
        'is_phone_verified',
    )
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)

    # Fieldsets for the change form
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            'Personal Info',
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'phone',
                    'avatar_url',
                    'city',
                    'state',
                ),
            },
        ),
        (
            'Role & Status',
            {
                'fields': (
                    'role',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'is_email_verified',
                    'is_phone_verified',
                ),
            },
        ),
        (
            'Notifications',
            {
                'fields': ('email_notifications', 'sms_notifications'),
            },
        ),
        (
            'Important dates',
            {
                'fields': ('last_login', 'date_joined'),
            },
        ),
        (
            'Permissions',
            {
                'fields': ('groups', 'user_permissions'),
                'classes': ('collapse',),
            },
        ),
    )

    # Fieldsets for the add form
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'first_name',
                    'last_name',
                    'role',
                    'password1',
                    'password2',
                ),
            },
        ),
    )


@admin.register(CustomerPreference)
class CustomerPreferenceAdmin(admin.ModelAdmin):
    """Admin configuration for customer recommendation preferences."""

    list_display = (
        'user',
        'preferred_city',
        'preferred_state',
        'budget_min',
        'budget_max',
        'preferred_capacity',
    )
    list_filter = ('preferred_city', 'preferred_state')
    search_fields = ('user__email', 'preferred_city')
    raw_id_fields = ('user',)


@admin.register(FavouriteHall)
class FavouriteHallAdmin(admin.ModelAdmin):
    """Admin configuration for customer favourite halls."""

    list_display = ('user', 'hall_id', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email',)
    raw_id_fields = ('user',)

