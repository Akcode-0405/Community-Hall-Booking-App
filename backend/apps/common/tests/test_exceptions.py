"""
Tests for apps.common custom exceptions and custom exception handler.
"""
from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError as DRFValidationError,
)

from apps.common.exceptions import (
    BookingConflictError,
    InvalidStateTransitionError,
    PaymentVerificationError,
    ResourceConflictError,
    SubscriptionLimitExceeded,
    SubscriptionRequiredError,
    TenantAccessDenied,
    custom_exception_handler,
)


class TestCustomExceptionHandler:
    """Test standard response structure for various exception types."""

    def test_drf_validation_error(self):
        exc = DRFValidationError({"email": ["Enter a valid email address."]})
        context = {"view": "TestView"}
        response = custom_exception_handler(exc, context)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data
        assert response.data["error"]["code"] == "VALIDATION_ERROR"
        assert "email" in response.data["error"]["details"]

    def test_django_validation_error(self):
        exc = DjangoValidationError({"phone": ["Invalid Indian phone number."]})
        context = {"view": "TestView"}
        response = custom_exception_handler(exc, context)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"]["code"] == "VALIDATION_ERROR"
        assert "phone" in response.data["error"]["details"]

    def test_not_authenticated(self):
        exc = NotAuthenticated("Authentication credentials were not provided.")
        context = {"view": "TestView"}
        response = custom_exception_handler(exc, context)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error"]["code"] == "NOT_AUTHENTICATED"

    def test_permission_denied(self):
        exc = PermissionDenied("You do not have permission.")
        context = {"view": "TestView"}
        response = custom_exception_handler(exc, context)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["error"]["code"] == "PERMISSION_DENIED"

    def test_http_404(self):
        exc = Http404("Resource not found.")
        context = {"view": "TestView"}
        response = custom_exception_handler(exc, context)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error"]["code"] == "NOT_FOUND"

    def test_custom_domain_exceptions(self):
        exceptions_to_test = [
            (TenantAccessDenied(), status.HTTP_403_FORBIDDEN, "TENANT_ACCESS_DENIED"),
            (SubscriptionRequiredError(), status.HTTP_403_FORBIDDEN, "SUBSCRIPTION_REQUIRED"),
            (SubscriptionLimitExceeded(), status.HTTP_403_FORBIDDEN, "SUBSCRIPTION_LIMIT_EXCEEDED"),
            (ResourceConflictError(), status.HTTP_409_CONFLICT, "RESOURCE_CONFLICT"),
            (BookingConflictError(), status.HTTP_409_CONFLICT, "BOOKING_CONFLICT"),
            (InvalidStateTransitionError(), status.HTTP_400_BAD_REQUEST, "INVALID_STATE_TRANSITION"),
            (PaymentVerificationError(), status.HTTP_400_BAD_REQUEST, "PAYMENT_VERIFICATION_FAILED"),
        ]

        for exc, expected_status, expected_code in exceptions_to_test:
            response = custom_exception_handler(exc, {"view": "TestView"})
            assert response.status_code == expected_status
            assert response.data["error"]["code"] == expected_code

    def test_unhandled_exception_returns_500(self):
        exc = RuntimeError("Database deadlocked")
        context = {"view": "TestView"}
        response = custom_exception_handler(exc, context)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data["error"]["code"] == "INTERNAL_SERVER_ERROR"

