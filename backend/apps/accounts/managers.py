"""
Custom user manager for email-based authentication.

Design Decisions:
- Email is the primary identifier (no username field).
- Superusers are automatically assigned the 'platform_admin' role.
- Default is_active=True so newly created users can log in immediately.
"""
from __future__ import annotations

from typing import Any

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom user manager supporting email-based authentication.

    Overrides create_user and create_superuser to use email
    instead of username as the unique identifier.
    """

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> Any:
        """
        Create and return a regular user with the given email and password.

        Args:
            email: The user's email address (will be normalized).
            password: The user's password (will be hashed).
            **extra_fields: Additional fields to set on the user model.

        Returns:
            The newly created User instance.

        Raises:
            ValueError: If email is not provided.
        """
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> Any:
        """
        Create and return a superuser with the given email and password.

        Superusers are automatically assigned:
        - is_staff=True
        - is_superuser=True
        - role='platform_admin'

        Args:
            email: The superuser's email address.
            password: The superuser's password.
            **extra_fields: Additional fields to set on the user model.

        Returns:
            The newly created superuser User instance.

        Raises:
            ValueError: If is_staff or is_superuser is not True.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'platform_admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

