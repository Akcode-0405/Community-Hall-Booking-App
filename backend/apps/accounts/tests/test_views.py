"""
Tests for apps.accounts API endpoints.
"""
from __future__ import annotations

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomerPreference, User, UserRole
from apps.accounts.services import AuthService
from apps.accounts.tests.factories import CustomerFactory, UserFactory, VendorFactory


@pytest.fixture
def auth_client():
    """Return an API client authenticated with a customer user."""
    client = APIClient()
    user = CustomerFactory(password="TestPass123!")
    tokens = AuthService.get_tokens_for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    client.user = user
    return client


@pytest.mark.django_db
class TestRegistrationView:
    """Tests for POST /api/v1/auth/register/"""

    url = reverse("accounts:register")

    def test_register_customer_success(self, api_client):
        data = {
            "email": "customer.reg@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Amit",
            "last_name": "Kumar",
            "phone": "+919876543210",
            "role": "customer",
        }
        response = api_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "user" in response.data
        assert "tokens" in response.data
        assert response.data["user"]["email"] == "customer.reg@example.com"
        assert response.data["user"]["role"] == "customer"
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]

        user = User.objects.get(email="customer.reg@example.com")
        assert user.check_password("StrongPassword123!") is True
        assert hasattr(user, "preferences")

    def test_register_vendor_success(self, api_client):
        data = {
            "email": "vendor.reg@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Pooja",
            "last_name": "Decorators",
            "role": "vendor",
        }
        response = api_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["role"] == "vendor"

    def test_register_password_mismatch(self, api_client):
        data = {
            "email": "mismatch@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "DifferentPassword123!",
            "first_name": "Amit",
            "last_name": "Kumar",
        }
        response = api_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, api_client):
        UserFactory(email="existing@example.com")
        data = {
            "email": "existing@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Amit",
            "last_name": "Kumar",
        }
        response = api_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_disallowed_role(self, api_client):
        data = {
            "email": "hacker@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Evil",
            "last_name": "User",
            "role": "platform_admin",
        }
        response = api_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLoginLogoutView:
    """Tests for login, logout, and token refresh."""

    login_url = reverse("accounts:login")
    logout_url = reverse("accounts:logout")
    refresh_url = reverse("accounts:token-refresh")

    def test_login_success(self, api_client):
        user = CustomerFactory(email="login.test@example.com", password="CorrectPassword123!")
        response = api_client.post(
            self.login_url,
            {"email": "login.test@example.com", "password": "CorrectPassword123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "tokens" in response.data
        assert "user" in response.data
        assert response.data["user"]["id"] == str(user.id)

    def test_login_invalid_password(self, api_client):
        CustomerFactory(email="login.fail@example.com", password="CorrectPassword123!")
        response = api_client.post(
            self.login_url,
            {"email": "login.fail@example.com", "password": "WrongPassword!"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, api_client):
        CustomerFactory(email="inactive@example.com", password="Password123!", is_active=False)
        response = api_client.post(
            self.login_url,
            {"email": "inactive@example.com", "password": "Password123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_token_refresh(self, api_client):
        user = CustomerFactory()
        tokens = AuthService.get_tokens_for_user(user)

        response = api_client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_logout_blacklists_token(self, auth_client):
        tokens = AuthService.get_tokens_for_user(auth_client.user)
        response = auth_client.post(
            self.logout_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # Trying to refresh with blacklisted token should now fail
        client = APIClient()
        refresh_res = client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )
        assert refresh_res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfileView:
    """Tests for GET and PATCH /api/v1/auth/me/"""

    url = reverse("accounts:profile")

    def test_get_profile_authenticated(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == auth_client.user.email
        assert response.data["full_name"] == auth_client.user.full_name

    def test_get_profile_unauthenticated(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_profile(self, auth_client):
        update_data = {
            "first_name": "NewFirst",
            "last_name": "NewLast",
            "city": "Mumbai",
            "state": "Maharashtra",
        }
        response = auth_client.patch(self.url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "NewFirst"
        assert response.data["city"] == "Mumbai"

        auth_client.user.refresh_from_db()
        assert auth_client.user.first_name == "NewFirst"


@pytest.mark.django_db
class TestPasswordManagementViews:
    """Tests for password change and reset endpoints."""

    change_pw_url = reverse("accounts:change-password")
    reset_request_url = reverse("accounts:password-reset")
    reset_confirm_url = reverse("accounts:password-reset-confirm")

    def test_change_password_success(self, auth_client):
        data = {
            "old_password": "TestPass123!",
            "new_password": "BrandNewPassword123!",
            "new_password_confirm": "BrandNewPassword123!",
        }
        response = auth_client.post(self.change_pw_url, data, format="json")
        assert response.status_code == status.HTTP_200_OK

        auth_client.user.refresh_from_db()
        assert auth_client.user.check_password("BrandNewPassword123!") is True

    def test_change_password_incorrect_old(self, auth_client):
        data = {
            "old_password": "WrongOldPassword!",
            "new_password": "BrandNewPassword123!",
            "new_password_confirm": "BrandNewPassword123!",
        }
        response = auth_client.post(self.change_pw_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_request_always_200(self, api_client):
        # Existing email
        user = CustomerFactory(email="registered@example.com")
        res1 = api_client.post(self.reset_request_url, {"email": "registered@example.com"}, format="json")
        assert res1.status_code == status.HTTP_200_OK

        # Non-existing email (anti-enumeration check)
        res2 = api_client.post(self.reset_request_url, {"email": "doesnotexist@example.com"}, format="json")
        assert res2.status_code == status.HTTP_200_OK

    def test_password_reset_confirm_success(self, api_client):
        user = CustomerFactory(password="oldpass123")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        data = {
            "uid": uid,
            "token": token,
            "new_password": "ResetPassword123!",
            "new_password_confirm": "ResetPassword123!",
        }
        response = api_client.post(self.reset_confirm_url, data, format="json")
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.check_password("ResetPassword123!") is True


@pytest.mark.django_db
class TestCustomerPreferenceView:
    """Tests for GET and PATCH /api/v1/auth/preferences/"""

    url = reverse("accounts:customer-preferences")

    def test_get_preferences_for_customer(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "weight_budget" in response.data
        assert response.data["weight_budget"] == 30

    def test_patch_preferences(self, auth_client):
        data = {
            "preferred_city": "Chennai",
            "budget_min": 60000,
            "budget_max": 150000,
            "weight_budget": 40,
            "weight_rating": 25,
        }
        response = auth_client.patch(self.url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["preferred_city"] == "Chennai"
        assert float(response.data["budget_min"]) == 60000.0
        assert response.data["weight_budget"] == 40
        assert response.data["weight_rating"] == 25

    def test_patch_preferences_invalid_budget_range(self, auth_client):
        data = {
            "budget_min": 200000,
            "budget_max": 50000,  # min > max
        }
        response = auth_client.patch(self.url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_preferences_denied_for_vendor(self):
        client = APIClient()
        vendor = VendorFactory(password="VendorPass123!")
        tokens = AuthService.get_tokens_for_user(vendor)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

