"""
Shared utility functions for the Hall Booking SaaS Platform.

These functions are used across multiple apps and are intentionally kept
free of model imports to avoid circular dependencies.
"""

from __future__ import annotations

import math
import random
import re
import string
from datetime import datetime
from typing import TYPE_CHECKING

from django.utils import timezone

if TYPE_CHECKING:
    from django.http import HttpRequest


# ---------------------------------------------------------------------------
# Reference number generators
# ---------------------------------------------------------------------------


def generate_booking_number(prefix: str = "BK") -> str:
    """
    Generate a unique booking reference number.

    Format: ``BK-2024-XXXXX`` where XXXXX is a random alphanumeric
    string (uppercase).

    Args:
        prefix: Prefix for the booking number. Defaults to ``"BK"``.

    Returns:
        A booking reference number string, e.g. ``"BK-2024-A3F7K"``.

    Example::

        >>> generate_booking_number()
        'BK-2024-A3F7K'
        >>> generate_booking_number(prefix="EVT")
        'EVT-2024-X9B2M'
    """
    year = timezone.now().year
    random_part = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=5)  # noqa: S311
    )
    return f"{prefix}-{year}-{random_part}"


def generate_invoice_number(prefix: str = "INV") -> str:
    """
    Generate a unique invoice reference number.

    Format: ``INV-2024-XXXXXXXX`` where XXXXXXXX is a random
    alphanumeric string (uppercase, 8 chars for lower collision risk).

    Args:
        prefix: Prefix for the invoice number. Defaults to ``"INV"``.

    Returns:
        An invoice reference number string, e.g. ``"INV-2024-A3F7K9B2"``.
    """
    year = timezone.now().year
    random_part = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=8)  # noqa: S311
    )
    return f"{prefix}-{year}-{random_part}"


# ---------------------------------------------------------------------------
# Request utilities
# ---------------------------------------------------------------------------


def get_client_ip(request: HttpRequest) -> str:
    """
    Extract the client IP address from the request.

    Checks ``X-Forwarded-For`` header first (for proxied requests),
    then falls back to ``REMOTE_ADDR``.

    Args:
        request: The Django HTTP request object.

    Returns:
        The client IP address as a string.

    Note:
        ``X-Forwarded-For`` can contain multiple IPs when the request
        passes through multiple proxies.  We take the first (leftmost)
        IP which is the original client.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # X-Forwarded-For: client, proxy1, proxy2
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


# ---------------------------------------------------------------------------
# Validation utilities
# ---------------------------------------------------------------------------

# Indian phone numbers: 10 digits starting with 6-9.
_INDIAN_PHONE_REGEX = re.compile(r"^[6-9]\d{9}$")

# Indian PIN codes: exactly 6 digits, first digit cannot be 0.
_PIN_CODE_REGEX = re.compile(r"^[1-9]\d{5}$")


def validate_indian_phone(phone: str) -> bool:
    """
    Validate an Indian mobile phone number.

    Accepts exactly 10 digits starting with 6, 7, 8, or 9.
    Does NOT accept country code prefix (+91) — strip it before calling.

    Args:
        phone: The phone number string to validate (digits only).

    Returns:
        ``True`` if valid, ``False`` otherwise.

    Examples::

        >>> validate_indian_phone("9876543210")
        True
        >>> validate_indian_phone("1234567890")
        False
        >>> validate_indian_phone("98765")
        False
    """
    if not phone:
        return False
    # Strip any leading +91 or 0 prefix for convenience.
    cleaned = phone.lstrip("+")
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]
    return bool(_INDIAN_PHONE_REGEX.match(cleaned))


def validate_pin_code(pin_code: str) -> bool:
    """
    Validate an Indian postal PIN code.

    Accepts exactly 6 digits where the first digit is 1-9.

    Args:
        pin_code: The PIN code string to validate.

    Returns:
        ``True`` if valid, ``False`` otherwise.

    Examples::

        >>> validate_pin_code("110001")
        True
        >>> validate_pin_code("012345")
        False
        >>> validate_pin_code("1234")
        False
    """
    if not pin_code:
        return False
    return bool(_PIN_CODE_REGEX.match(pin_code))


# ---------------------------------------------------------------------------
# Geo utilities
# ---------------------------------------------------------------------------


def calculate_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate the great-circle distance between two points using the
    Haversine formula.

    Args:
        lat1: Latitude of point 1 in decimal degrees.
        lon1: Longitude of point 1 in decimal degrees.
        lat2: Latitude of point 2 in decimal degrees.
        lon2: Longitude of point 2 in decimal degrees.

    Returns:
        Distance in kilometres (float).

    Note:
        For precise geo queries at scale, prefer PostGIS
        ``ST_Distance`` / ``ST_DWithin``.  This function is useful
        for quick client-side or non-critical distance calculations.

    Examples::

        >>> round(calculate_distance_km(28.6139, 77.2090, 19.0760, 72.8777), 1)
        1153.3
    """
    # Earth's mean radius in km
    R = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
