"""
Django validators for the Hall Booking SaaS Platform.

Reusable field validators for common Indian locale data formats and
file upload constraints.  Use these in model field definitions or
serializer fields.

Example usage in a model::

    from apps.common.validators import IndianPhoneNumberValidator, PinCodeValidator

    class Address(BaseModel):
        phone = models.CharField(
            max_length=15,
            validators=[IndianPhoneNumberValidator()],
        )
        pin_code = models.CharField(
            max_length=6,
            validators=[PinCodeValidator()],
        )
"""

from __future__ import annotations

import re
from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible


# ---------------------------------------------------------------------------
# Phone & PIN code validators
# ---------------------------------------------------------------------------


@deconstructible
class IndianPhoneNumberValidator(RegexValidator):
    """
    Validate Indian mobile phone numbers.

    Accepted format: exactly 10 digits starting with 6, 7, 8, or 9.
    Country code (+91) and leading zero should be stripped before validation.

    Examples of valid numbers:
        - 9876543210
        - 6123456789

    Examples of invalid numbers:
        - 1234567890 (starts with 1)
        - 98765 (too short)
        - 98765432101 (too long)
    """

    regex = r"^[6-9]\d{9}$"
    message = (
        "Enter a valid Indian mobile phone number. "
        "It must be 10 digits starting with 6, 7, 8, or 9."
    )
    code = "invalid_phone_number"


@deconstructible
class PinCodeValidator(RegexValidator):
    """
    Validate Indian postal PIN codes.

    Accepted format: exactly 6 digits where the first digit is 1-9.

    Examples of valid PIN codes:
        - 110001 (New Delhi)
        - 400001 (Mumbai)

    Examples of invalid PIN codes:
        - 012345 (starts with 0)
        - 1234 (too short)
    """

    regex = r"^[1-9]\d{5}$"
    message = (
        "Enter a valid Indian PIN code. "
        "It must be exactly 6 digits and cannot start with 0."
    )
    code = "invalid_pin_code"


# ---------------------------------------------------------------------------
# File upload validators
# ---------------------------------------------------------------------------


@deconstructible
class FileSizeValidator:
    """
    Validate that an uploaded file does not exceed a maximum size.

    Args:
        max_size_mb: Maximum allowed file size in megabytes.

    Example::

        class HallImage(BaseModel):
            image = models.ImageField(
                upload_to='halls/',
                validators=[FileSizeValidator(max_size_mb=5)],
            )
    """

    def __init__(self, max_size_mb: float = 5.0) -> None:
        self.max_size_mb = max_size_mb
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)

    def __call__(self, value: Any) -> None:
        if value.size > self.max_size_bytes:
            raise ValidationError(
                f"File size must not exceed {self.max_size_mb} MB. "
                f"Current file size: {value.size / (1024 * 1024):.2f} MB.",
                code="file_too_large",
            )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FileSizeValidator):
            return NotImplemented
        return self.max_size_mb == other.max_size_mb

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(max_size_mb={self.max_size_mb})"


@deconstructible
class ImageDimensionValidator:
    """
    Validate that an uploaded image meets minimum dimension requirements.

    Args:
        min_width: Minimum width in pixels.
        min_height: Minimum height in pixels.

    Example::

        class HallImage(BaseModel):
            image = models.ImageField(
                upload_to='halls/',
                validators=[ImageDimensionValidator(min_width=800, min_height=600)],
            )

    Note:
        This validator requires Pillow to read image dimensions.  It
        operates on the uploaded file object which must have ``width``
        and ``height`` attributes (as Django's ``ImageField`` provides).
    """

    def __init__(self, min_width: int = 200, min_height: int = 200) -> None:
        self.min_width = min_width
        self.min_height = min_height

    def __call__(self, value: Any) -> None:
        # Django's ImageField populates width/height on the file object.
        # For other file types, we need to read dimensions manually.
        width = getattr(value, "width", None)
        height = getattr(value, "height", None)

        if width is None or height is None:
            try:
                from PIL import Image

                value.seek(0)
                img = Image.open(value)
                width, height = img.size
                value.seek(0)
            except (ImportError, Exception):
                # Cannot determine dimensions; skip validation rather
                # than blocking the upload.
                return

        errors: list[str] = []
        if width < self.min_width:
            errors.append(
                f"Image width must be at least {self.min_width}px "
                f"(got {width}px)."
            )
        if height < self.min_height:
            errors.append(
                f"Image height must be at least {self.min_height}px "
                f"(got {height}px)."
            )

        if errors:
            raise ValidationError(errors, code="image_too_small")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ImageDimensionValidator):
            return NotImplemented
        return (
            self.min_width == other.min_width
            and self.min_height == other.min_height
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(min_width={self.min_width}, min_height={self.min_height})"
        )
