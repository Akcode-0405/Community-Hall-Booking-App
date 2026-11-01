"""
Token generators for the accounts app.

Email verification uses its own generator (distinct ``key_salt``) so a
verification token can never be replayed as a password-reset token, and
vice versa. Including ``is_email_verified`` in the hash makes the link
single-use: once the email is verified, the token stops validating.
"""
from __future__ import annotations

from typing import Any

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Signed, expiring token for email-verification links."""

    key_salt = 'apps.accounts.tokens.EmailVerificationTokenGenerator'

    def _make_hash_value(self, user: Any, timestamp: int) -> str:
        return f"{user.pk}{user.email}{user.is_email_verified}{timestamp}"


email_verification_token_generator = EmailVerificationTokenGenerator()
