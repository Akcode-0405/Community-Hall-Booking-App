"""
Celery tasks for the accounts app.

All email-sending operations are offloaded to Celery for async processing.
This prevents the API from blocking while emails are being sent and provides
automatic retry on transient failures (e.g., SMTP connection issues).

Each task uses ``bind=True`` to access the task instance for retry logic,
and ``max_retries=3`` with exponential backoff.
"""
from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_password_reset_email_task(self, user_id: str, reset_url: str) -> None:
    """
    Send a password reset email asynchronously.

    Args:
        self: The Celery task instance (bound).
        user_id: UUID string of the user requesting the reset.
        reset_url: The full password reset URL with token and uid.
    """
    from apps.accounts.models import User

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error("Password reset email task: user %s not found", user_id)
        return

    subject = 'Reset Your Password — Hall Booking Platform'
    message = (
        f"Hi {user.first_name},\n\n"
        f"You requested a password reset. Click the link below to set a new password:\n\n"
        f"{reset_url}\n\n"
        f"If you didn't request this, please ignore this email.\n\n"
        f"This link will expire in 24 hours.\n\n"
        f"— Hall Booking Platform Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL
            if hasattr(settings, 'DEFAULT_FROM_EMAIL')
            else 'noreply@hallbooking.com',
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("Password reset email sent to: %s", user.email)
    except Exception as exc:
        logger.error(
            "Failed to send password reset email to %s: %s",
            user.email,
            str(exc),
        )
        # Retry with exponential backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_welcome_email_task(self, user_id: str) -> None:
    """
    Send a welcome email after user registration.

    Args:
        self: The Celery task instance (bound).
        user_id: UUID string of the newly registered user.
    """
    from apps.accounts.models import User

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error("Welcome email task: user %s not found", user_id)
        return

    subject = 'Welcome to Hall Booking Platform!'
    message = (
        f"Hi {user.first_name},\n\n"
        f"Welcome to the Hall Booking Platform! We're glad to have you.\n\n"
        f"You can now browse and book community halls for your events.\n\n"
        f"— Hall Booking Platform Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL
            if hasattr(settings, 'DEFAULT_FROM_EMAIL')
            else 'noreply@hallbooking.com',
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("Welcome email sent to: %s", user.email)
    except Exception as exc:
        logger.error(
            "Failed to send welcome email to %s: %s",
            user.email,
            str(exc),
        )
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_email_verification_task(self, user_id: str) -> None:
    """
    Send an email verification link to the user.

    Args:
        self: The Celery task instance (bound).
        user_id: UUID string of the user to verify.
    """
    from django.utils.encoding import force_bytes
    from django.utils.http import urlsafe_base64_encode

    from apps.accounts.models import User
    from apps.accounts.tokens import email_verification_token_generator

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error("Email verification task: user %s not found", user_id)
        return

    if user.is_email_verified:
        logger.info("Email verification skipped; already verified: %s", user.email)
        return

    # Dedicated generator — NOT the password-reset generator, otherwise a
    # verification link could be used to reset the password.
    token = email_verification_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    verify_url = f"{frontend_url}/auth/verify-email?uid={uid}&token={token}"

    subject = 'Verify Your Email — Hall Booking Platform'
    message = (
        f"Hi {user.first_name},\n\n"
        f"Please verify your email address by clicking the link below:\n\n"
        f"{verify_url}\n\n"
        f"If you didn't create this account, please ignore this email.\n\n"
        f"— Hall Booking Platform Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL
            if hasattr(settings, 'DEFAULT_FROM_EMAIL')
            else 'noreply@hallbooking.com',
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("Email verification sent to: %s", user.email)
    except Exception as exc:
        logger.error(
            "Failed to send email verification to %s: %s",
            user.email,
            str(exc),
        )
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

