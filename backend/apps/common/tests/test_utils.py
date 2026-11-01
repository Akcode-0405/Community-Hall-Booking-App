"""
Tests for apps.common utility functions.
"""
from __future__ import annotations

import re
from unittest.mock import MagicMock

import pytest

from apps.common.utils import (
    calculate_distance_km,
    generate_booking_number,
    generate_invoice_number,
    get_client_ip,
    validate_indian_phone,
    validate_pin_code,
)


class TestReferenceGenerators:
    """Test booking and invoice reference number generators."""

    def test_generate_booking_number_format(self):
        """Booking number follows BK-YYYY-XXXXX format."""
        num = generate_booking_number()
        pattern = r"^BK-\d{4}-[A-Z0-9]{5}$"
        assert re.match(pattern, num) is not None

    def test_generate_booking_number_custom_prefix(self):
        """Custom prefix is respected."""
        num = generate_booking_number(prefix="HAL")
        assert num.startswith("HAL-")

    def test_generate_booking_number_uniqueness(self):
        """Consecutively generated numbers should be distinct."""
        numbers = {generate_booking_number() for _ in range(50)}
        assert len(numbers) == 50

    def test_generate_invoice_number_format(self):
        """Invoice number follows INV-YYYY-XXXXXXXX format."""
        num = generate_invoice_number()
        pattern = r"^INV-\d{4}-[A-Z0-9]{8}$"
        assert re.match(pattern, num) is not None

    def test_generate_invoice_number_custom_prefix(self):
        """Custom prefix for invoice number is respected."""
        num = generate_invoice_number(prefix="TAX")
        assert num.startswith("TAX-")


class TestClientIpExtractor:
    """Test get_client_ip extraction from various request headers."""

    def test_ip_from_remote_addr(self):
        """Extract IP when only REMOTE_ADDR is present."""
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "192.168.1.10"}
        assert get_client_ip(request) == "192.168.1.10"

    def test_ip_from_x_forwarded_for_single(self):
        """Extract IP from X-Forwarded-For header with single IP."""
        request = MagicMock()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "203.0.113.195",
            "REMOTE_ADDR": "10.0.0.1",
        }
        assert get_client_ip(request) == "203.0.113.195"

    def test_ip_from_x_forwarded_for_multiple(self):
        """Extract original client (first leftmost IP) when multiple proxies exist."""
        request = MagicMock()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "203.0.113.195, 70.41.3.18, 150.172.238.178",
            "REMOTE_ADDR": "10.0.0.1",
        }
        assert get_client_ip(request) == "203.0.113.195"

    def test_ip_fallback_to_zero(self):
        """Fallback to 0.0.0.0 if neither header is present."""
        request = MagicMock()
        request.META = {}
        assert get_client_ip(request) == "0.0.0.0"


class TestValidationUtils:
    """Test Indian phone number and PIN code validators."""

    @pytest.mark.parametrize(
        "phone,expected",
        [
            ("9876543210", True),
            ("+919876543210", True),
            ("919876543210", True),
            ("09876543210", True),
            ("8123456789", True),
            ("7123456789", True),
            ("6123456789", True),
            ("5123456789", False),  # doesn't start with 6-9
            ("98765", False),       # too short
            ("9876543210123", False),  # too long
            ("abcdefghij", False),  # non-digits
            ("", False),
        ],
    )
    def test_validate_indian_phone(self, phone, expected):
        assert validate_indian_phone(phone) == expected

    @pytest.mark.parametrize(
        "pin,expected",
        [
            ("560001", True),   # Bangalore
            ("110001", True),   # New Delhi
            ("600001", True),   # Chennai
            ("012345", False),  # starts with 0
            ("56000", False),   # 5 digits
            ("5600001", False), # 7 digits
            ("56000A", False),  # alphanumeric
            ("", False),
        ],
    )
    def test_validate_pin_code(self, pin, expected):
        assert validate_pin_code(pin) == expected


class TestGeoUtils:
    """Test Haversine distance calculation."""

    def test_calculate_distance_same_point(self):
        """Distance between identical points should be 0."""
        dist = calculate_distance_km(12.9716, 77.5946, 12.9716, 77.5946)
        assert round(dist, 2) == 0.0

    def test_calculate_distance_known_cities(self):
        """
        Distance between Delhi (28.6139, 77.2090) and Mumbai (19.0760, 72.8777).
        Known great-circle distance is approx 1153 km.
        """
        dist = calculate_distance_km(28.6139, 77.2090, 19.0760, 72.8777)
        assert 1140 < dist < 1170

