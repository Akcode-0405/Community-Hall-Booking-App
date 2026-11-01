"""
Custom DRF exception handler and exception classes.

Provides a consistent error response format across the entire API::

    {
        "error": {
            "code": "BOOKING_CONFLICT",
            "message": "The requested time slot is already booked.",
            "details": {
                "conflicting_booking_id": "..."
            }
        }
    }

All custom exceptions inherit from DRF's ``APIException`` so they
integrate seamlessly with DRF's exception handling pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exception handler
# ---------------------------------------------------------------------------


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Wrap DRF's default exception handler to produce consistent error
    response bodies.

    Handles:
        - DRF exceptions (validation, auth, permission, throttle, etc.)
        - Django's ``ValidationError`` (converted to DRF format)
        - ``Http404`` (converted to a structured 404)
        - Unhandled exceptions (logged + returned as 500)

    Response format::

        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input.",
                "details": { ... }
            }
        }
    """
    # Convert Django ValidationError to DRF ValidationError so it's
    # handled uniformly.
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = DRFValidationError(detail=exc.message_dict)
        else:
            exc = DRFValidationError(detail=exc.messages)

    # Let DRF handle the exception first.
    response = drf_exception_handler(exc, context)

    if response is not None:
        error_data = _build_error_payload(exc, response)
        response.data = error_data
        return response

    # Unhandled exception — log it and return a generic 500.
    logger.exception(
        "Unhandled exception in %s: %s",
        context.get("view", "unknown_view"),
        exc,
    )
    return Response(
        {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {},
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _build_error_payload(
    exc: Exception,
    response: Response,
) -> dict[str, Any]:
    """
    Build the structured error payload from the exception and response.
    """
    code = _get_error_code(exc, response)
    message = _get_error_message(exc)
    details = _get_error_details(exc, response)

    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }


def _get_error_code(exc: Exception, response: Response) -> str:
    """Determine an error code string from the exception type."""
    if isinstance(exc, DRFValidationError):
        return "VALIDATION_ERROR"
    if isinstance(exc, NotAuthenticated):
        return "NOT_AUTHENTICATED"
    if isinstance(exc, AuthenticationFailed):
        return "AUTHENTICATION_FAILED"
    if isinstance(exc, PermissionDenied):
        return "PERMISSION_DENIED"
    if isinstance(exc, Http404):
        return "NOT_FOUND"

    # Custom exceptions carry their own code attribute.
    if hasattr(exc, "default_code"):
        return str(exc.default_code).upper()

    # Fall back to HTTP status-based codes.
    status_code_map: dict[int, str] = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        429: "THROTTLED",
    }
    return status_code_map.get(response.status_code, "ERROR")


def _get_error_message(exc: Exception) -> str:
    """Extract a human-readable message from the exception."""
    if hasattr(exc, "detail"):
        detail = exc.detail  # type: ignore[union-attr]
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list):
            return "; ".join(str(d) for d in detail)
        # For dict details (field-level errors), return a summary.
        return "Validation failed. Check details for specific field errors."
    return str(exc)


def _get_error_details(exc: Exception, response: Response) -> dict[str, Any] | list[Any]:
    """Extract structured details from the exception."""
    if isinstance(exc, DRFValidationError):
        detail = exc.detail
        if isinstance(detail, dict):
            return detail  # type: ignore[return-value]
        if isinstance(detail, list):
            return {"errors": detail}
    return {}


# ---------------------------------------------------------------------------
# Custom exception classes
# ---------------------------------------------------------------------------


class TenantAccessDenied(APIException):
    """
    Raised when a user attempts to access a resource from a different tenant.

    HTTP 403 Forbidden.
    """

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to access this tenant's resources."
    default_code = "tenant_access_denied"


class SubscriptionRequiredError(APIException):
    """
    Raised when an action requires an active subscription but the
    tenant's subscription is missing or expired.

    HTTP 403 Forbidden.
    """

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = (
        "An active subscription is required to perform this action. "
        "Please renew your subscription."
    )
    default_code = "subscription_required"


class SubscriptionLimitExceeded(APIException):
    """
    Raised when a tenant exceeds a limit defined by their subscription plan.

    Examples: max halls, max bookings per month, max storage.

    HTTP 403 Forbidden.
    """

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = (
        "You have reached the limit for your current subscription plan. "
        "Please upgrade to continue."
    )
    default_code = "subscription_limit_exceeded"


class ResourceConflictError(APIException):
    """
    Raised when a create or update would conflict with existing data.

    HTTP 409 Conflict.
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = "The requested operation conflicts with existing data."
    default_code = "resource_conflict"


class BookingConflictError(ResourceConflictError):
    """
    Raised when a booking time slot overlaps with an existing booking.

    HTTP 409 Conflict.

    Example::

        raise BookingConflictError(
            detail="The requested time slot is already booked.",
            code="booking_conflict",
        )
    """

    default_detail = "The requested time slot conflicts with an existing booking."
    default_code = "booking_conflict"


class InvalidStateTransitionError(APIException):
    """
    Raised when a state transition is not allowed.

    For example, trying to cancel a booking that has already been completed.

    HTTP 400 Bad Request.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This state transition is not allowed."
    default_code = "invalid_state_transition"


class PaymentVerificationError(APIException):
    """
    Raised when payment verification with the payment gateway fails.

    HTTP 400 Bad Request.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Payment verification failed. Please contact support."
    default_code = "payment_verification_failed"
