"""
Tests for apps.common validators.
"""
from __future__ import annotations

import io
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError
from PIL import Image

from apps.common.validators import (
    FileSizeValidator,
    ImageDimensionValidator,
    IndianPhoneNumberValidator,
    PinCodeValidator,
)


class TestValidators:
    """Test custom validators."""

    def test_phone_validator_valid(self):
        validator = IndianPhoneNumberValidator()
        validator("9876543210")  # Should not raise

    def test_phone_validator_invalid(self):
        validator = IndianPhoneNumberValidator()
        with pytest.raises(ValidationError):
            validator("1234567890")

    def test_pin_code_validator_valid(self):
        validator = PinCodeValidator()
        validator("560001")  # Should not raise

    def test_pin_code_validator_invalid(self):
        validator = PinCodeValidator()
        with pytest.raises(ValidationError):
            validator("056001")

    def test_file_size_validator_within_limit(self):
        validator = FileSizeValidator(max_size_mb=2.0)
        file_mock = MagicMock()
        file_mock.size = 1024 * 1024  # 1 MB
        validator(file_mock)  # Should not raise

    def test_file_size_validator_exceeds_limit(self):
        validator = FileSizeValidator(max_size_mb=1.0)
        file_mock = MagicMock()
        file_mock.size = 2 * 1024 * 1024  # 2 MB
        with pytest.raises(ValidationError) as exc_info:
            validator(file_mock)
        assert "File size must not exceed 1.0 MB" in str(exc_info.value)

    def test_image_dimension_validator_valid(self):
        validator = ImageDimensionValidator(min_width=100, min_height=100)
        img_file = io.BytesIO()
        image = Image.new("RGB", (200, 200), color="red")
        image.save(img_file, format="JPEG")
        img_file.seek(0)

        validator(img_file)  # Should not raise

    def test_image_dimension_validator_too_small(self):
        validator = ImageDimensionValidator(min_width=300, min_height=300)
        img_file = io.BytesIO()
        image = Image.new("RGB", (150, 150), color="blue")
        image.save(img_file, format="JPEG")
        img_file.seek(0)

        with pytest.raises(ValidationError):
            validator(img_file)

