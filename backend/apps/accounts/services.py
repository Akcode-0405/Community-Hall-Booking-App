"""
Service layer for the accounts app.

Business logic is separated from views for:
- Testability: Services can be tested without HTTP request/response overhead.
- Reuse: Services can be called from views, management commands, Celery tasks, etc.
- Clarity: Views focus on request handling; services focus on business rules.
"""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import User
from .tokens import email_verification_token_generator

logger = logging.getLogger(__name__)


class AuthService:
    """Service class for authentication and user management operations."""

    @staticmethod
    def register_user(validated_data: dict[str, Any]) -> User:
        """
        Register a new user with the provided validated data.

        The password is hashed before storage via ``create_user``.

        Args:
            validated_data: Data that has already been validated by
                ``UserRegistrationSerializer``.

        Returns:
            The newly created User instance.
        """
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            **validated_data,
        )
        return user

    @staticmethod
    def get_tokens_for_user(user: User) -> dict[str, str]:
        """
        Generate JWT access and refresh tokens for a user.

        Uses djangorestframework-simplejwt's ``RefreshToken`` to create
        a token pair containing the user's ID claim.

        Args:
            user: The User instance to generate tokens for.

        Returns:
            A dict with 'refresh' and 'access' token strings.
        """
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def send_password_reset_email(email: str) -> None:
        """
        Send a password reset email if the user exists.

        Uses Django's ``PasswordResetTokenGenerator`` for secure, single-use
        tokens. The actual email sending is delegated to a Celery task for
        async processing.

        This method silently does nothing if the email doesn't exist,
        preventing email enumeration attacks.

        Args:
            email: The email address to send the reset link to.
        """
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            # Silently return to prevent email enumeration
            logger.info(
                "Password reset requested for non-existent email: %s",
                email,
            )
            return

        # Generate token and uid for the reset link
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Build the reset URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/auth/reset-password?uid={uid}&token={token}"

        # Queue the email as a Celery task once the transaction commits
        from django.db import transaction

        from .tasks import send_password_reset_email_task

        user_id = str(user.id)
        transaction.on_commit(
            lambda: send_password_reset_email_task.delay(user_id, reset_url)
        )
        logger.info("Password reset email queued for user: %s", user.email)

    @staticmethod
    def _user_from_uid(uid: str) -> User | None:
        """Decode a base64 uid from an emailed link into a User (or None)."""
        from django.core.exceptions import ValidationError

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            return User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, ValidationError, User.DoesNotExist):
            return None

    @staticmethod
    def send_verification_email(user: User) -> None:
        """Queue an email-verification link for the user (no-op if verified)."""
        if user.is_email_verified:
            return
        from django.db import transaction

        from .tasks import send_email_verification_task

        user_id = str(user.id)
        transaction.on_commit(lambda: send_email_verification_task.delay(user_id))

    @staticmethod
    def verify_email(uid: str, token: str) -> bool:
        """
        Mark the user's email as verified if the uid/token pair is valid.

        Returns:
            True on success, False for an invalid or expired link.
        """
        user = AuthService._user_from_uid(uid)
        if user is None:
            return False
        if not email_verification_token_generator.check_token(user, token):
            return False
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified', 'updated_at'])
        logger.info("Email verified for user: %s", user.email)
        return True

    @staticmethod
    def reset_password(uid: str, token: str, new_password: str) -> bool:
        """
        Validate a password reset token and set the new password.

        Args:
            uid: Base64-encoded user ID from the reset link.
            token: Password reset token from the reset link.
            new_password: The new password to set.

        Returns:
            True if password was reset successfully, False otherwise.
        """
        user = AuthService._user_from_uid(uid)
        if user is None:
            logger.warning("Password reset failed: invalid uid=%s", uid)
            return False

        if not default_token_generator.check_token(user, token):
            logger.warning(
                "Password reset failed: invalid token for user %s", user.email
            )
            return False

        user.set_password(new_password)
        user.save(update_fields=['password'])
        logger.info("Password reset successful for user: %s", user.email)
        return True

