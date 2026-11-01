"""
Serializers for the accounts app.

Provides serializers for user registration, authentication, profile management,
password management, and customer preferences.

Design Decisions:
- Registration is restricted to 'customer' and 'vendor' roles only.
  Admin/owner/manager roles are assigned through internal processes.
- Password validation uses Django's built-in validators for consistency.
- Email enumeration is prevented in password reset (always returns success).
- Profile update serializer is separate from read serializer to enforce
  which fields are editable.
"""
from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from .models import CustomerPreference, User, UserRole


class UserRegistrationSerializer(serializers.Serializer):
    """
    Serializer for new user registration.

    Only 'customer' and 'vendor' roles are allowed during self-registration.
    Other roles (platform_admin, tenant_owner, tenant_manager) are assigned
    through internal admin processes.
    """

    ALLOWED_ROLES = {UserRole.CUSTOMER, UserRole.VENDOR}

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = PhoneNumberField(required=False, allow_blank=True, region='IN')
    role = serializers.ChoiceField(
        choices=[
            (UserRole.CUSTOMER.value, UserRole.CUSTOMER.label),
            (UserRole.VENDOR.value, UserRole.VENDOR.label),
        ],
        default=UserRole.CUSTOMER.value,
    )

    def validate_email(self, value: str) -> str:
        """Ensure email is unique (case-insensitive)."""
        email = value.lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                'A user with this email address already exists.'
            )
        return email

    def validate_role(self, value: str) -> str:
        """Ensure only customer/vendor roles are allowed for self-registration."""
        if value not in self.ALLOWED_ROLES:
            raise serializers.ValidationError(
                f'Registration is only allowed for roles: '
                f'{", ".join(r.value for r in self.ALLOWED_ROLES)}.'
            )
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate that passwords match and meet strength requirements."""
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)

        if password != password_confirm:
            raise serializers.ValidationError(
                {'password_confirm': 'Passwords do not match.'}
            )

        # Run Django's password validators (with an unsaved user so the
        # similarity validator can compare against name/email).
        candidate = User(
            email=attrs.get('email', ''),
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', ''),
        )
        try:
            validate_password(password, user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {'password': list(exc.messages)}
            )

        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        """
        Create a new user with a properly hashed password.

        Args:
            validated_data: Validated registration data.

        Returns:
            The newly created User instance.
        """
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            **validated_data,
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login/authentication.

    Validates credentials and returns the authenticated user.
    """

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Authenticate the user with provided credentials.

        Checks:
        1. Credentials are valid.
        2. Account is active.
        """
        email = attrs.get('email', '').lower()
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                'Invalid email or password.',
                code='authentication_failed',
            )

        if not user.is_active:
            raise serializers.ValidationError(
                'This account has been deactivated.',
                code='account_inactive',
            )

        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Read serializer for user profile data.

    Exposes the user's public profile information including role,
    verification status, and notification preferences.
    """

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'avatar_url',
            'city',
            'state',
            'is_email_verified',
            'is_phone_verified',
            'email_notifications',
            'sms_notifications',
            'date_joined',
        ]
        read_only_fields = [
            'id',
            'email',
            'role',
            'is_email_verified',
            'is_phone_verified',
            'date_joined',
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile fields.

    Only allows modification of non-sensitive fields. Email, role, and
    verification status cannot be changed through this endpoint.
    """

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone',
            'avatar_url',
            'city',
            'state',
            'email_notifications',
            'sms_notifications',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for authenticated password change.

    Validates the old password, ensures new passwords match,
    and checks new password strength using Django's validators.
    """

    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_old_password(self, value: str) -> str:
        """Verify that the old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate that new passwords match and meet strength requirements."""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')

        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {'new_password_confirm': 'New passwords do not match.'}
            )

        # Run Django's password validators
        try:
            validate_password(new_password, user=self.context['request'].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {'new_password': list(exc.messages)}
            )

        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset email.

    Note: The view always returns a success response regardless of whether
    the email exists, to prevent email enumeration attacks.
    """

    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        """Normalize the email address."""
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a password reset.

    Validates the token/uid pair and the new password strength.
    """

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate that new passwords match and meet strength requirements."""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')

        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {'new_password_confirm': 'Passwords do not match.'}
            )

        # Run Django's password validators
        try:
            validate_password(new_password)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {'new_password': list(exc.messages)}
            )

        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """uid/token pair from an email-verification link."""

    uid = serializers.CharField()
    token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """Refresh token to blacklist on logout."""

    refresh = serializers.CharField()


class CustomerPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for customer recommendation preferences.

    Weight fields must be integers between 0 and 100 inclusive.
    The user, created_at, and updated_at fields are read-only.
    """

    WEIGHT_FIELDS = [
        'weight_budget',
        'weight_capacity',
        'weight_proximity',
        'weight_amenities',
        'weight_rating',
    ]

    class Meta:
        model = CustomerPreference
        fields = [
            'id',
            'user',
            'preferred_city',
            'preferred_state',
            'budget_min',
            'budget_max',
            'preferred_capacity',
            'preferred_hall_type',
            'weight_budget',
            'weight_capacity',
            'weight_proximity',
            'weight_amenities',
            'weight_rating',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate weights (0-100) and that budget_min <= budget_max."""
        budget_min = attrs.get('budget_min', getattr(self.instance, 'budget_min', None))
        budget_max = attrs.get('budget_max', getattr(self.instance, 'budget_max', None))
        if budget_min is not None and budget_max is not None and budget_min > budget_max:
            raise serializers.ValidationError(
                {'budget_max': 'budget_max must be greater than or equal to budget_min.'}
            )
        for field_name in self.WEIGHT_FIELDS:
            value = attrs.get(field_name)
            if value is not None and not (0 <= value <= 100):
                raise serializers.ValidationError(
                    {field_name: f'Weight must be between 0 and 100 (got {value}).'}
                )
        return attrs

