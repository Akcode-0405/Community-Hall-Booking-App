"""
Tests for apps.accounts services.
"""
from __future__ import annotations

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.accounts.models import User, UserRole
from apps.accounts.services import AuthService
from apps.accounts.tests.factories import CustomerFactory, UserFactory


@pytest.mark.django_db
class TestAuthService:
    """Test suite for AuthService business logic."""

    def test_register_user_creates_active_user(self):
        """register_user hashes password and creates user."""
        data = {
            "email": "register.service@example.com",
            "password": "Password123!",
            "first_name": "Rohan",
            "last_name": "Sharma",
            "role": UserRole.CUSTOMER,
        }
        user = AuthService.register_user(data)
        assert user.id is not None
        assert user.email == "register.service@example.com"
        assert user.check_password("Password123!") is True
        assert user.is_active is True

    def test_get_tokens_for_user(self):
        """get_tokens_for_user returns valid JWT access and refresh tokens."""
        user = CustomerFactory()
        tokens = AuthService.get_tokens_for_user(user)

        assert "access" in tokens
        assert "refresh" in tokens
        assert isinstance(tokens["access"], str)
        assert isinstance(tokens["refresh"], str)

    def test_reset_password_success(self):
        """reset_password succeeds with valid uid and token."""
        user = CustomerFactory(password="oldpassword123")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        result = AuthService.reset_password(uid, token, "NewPassword123!")
        assert result is True

        user.refresh_from_db()
        assert user.check_password("NewPassword123!") is True

    def test_reset_password_invalid_token(self):
        """reset_password fails with invalid token."""
        user = CustomerFactory()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        bad_token = "invalid-token-123"

        result = AuthService.reset_password(uid, bad_token, "NewPassword123!")
        assert result is False

    def test_reset_password_invalid_uid(self):
        """reset_password fails with non-existent uid."""
        bad_uid = urlsafe_base64_encode(force_bytes("00000000-0000-0000-0000-000000000000"))
        result = AuthService.reset_password(bad_uid, "some-token", "NewPassword123!")
        assert result is False

