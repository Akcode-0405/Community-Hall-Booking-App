"""
Views for the accounts app.

Provides REST API endpoints for:
- User registration and authentication (JWT)
- Profile retrieval and update
- Password change and reset
- Customer preference management

Design Decisions:
- Registration and login are AllowAny (public endpoints).
- All other endpoints require authentication (IsAuthenticated).
- Customer preferences use get_or_create to auto-initialize on first access.
- Password reset always returns 200 to prevent email enumeration.
- JWT tokens are returned on both registration and login for immediate use.
"""
from __future__ import annotations

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.throttling import AuthRateThrottle

from .models import CustomerPreference, UserRole
from .serializers import (
    ChangePasswordSerializer,
    CustomerPreferenceSerializer,
    EmailVerificationSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserRegistrationSerializer,
)
from .services import AuthService

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.

    **POST /auth/register/**

    Creates a new user with 'customer' or 'vendor' role and returns
    the user profile along with JWT access and refresh tokens.

    Permissions: AllowAny (public endpoint)
    """

    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Handle user registration and return profile with JWT tokens."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        AuthService.send_verification_email(user)
        tokens = AuthService.get_tokens_for_user(user)
        profile = UserProfileSerializer(user).data

        logger.info("New user registered: %s (role=%s)", user.email, user.role)

        return Response(
            {
                'user': profile,
                'tokens': tokens,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Authenticate a user and return JWT tokens.

    **POST /auth/login/**

    Validates email/password credentials and returns the user profile
    along with JWT access and refresh tokens.

    Permissions: AllowAny (public endpoint)
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(request=UserLoginSerializer)
    def post(self, request: Request) -> Response:
        """Handle user login and return profile with JWT tokens."""
        from django.contrib.auth.models import update_last_login

        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        update_last_login(None, user)
        tokens = AuthService.get_tokens_for_user(user)
        profile = UserProfileSerializer(user).data

        logger.info("User logged in: %s", user.email)

        return Response(
            {
                'user': profile,
                'tokens': tokens,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Logout a user by blacklisting their refresh token.

    **POST /auth/logout/**

    Requires the refresh token in the request body. The token is added
    to the blacklist so it can no longer be used to obtain new access tokens.

    Permissions: IsAuthenticated
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=LogoutSerializer)
    def post(self, request: Request) -> Response:
        """Blacklist the provided refresh token."""
        from rest_framework_simplejwt.exceptions import TokenError
        from rest_framework_simplejwt.tokens import RefreshToken

        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            # A user may only revoke their own refresh tokens.
            if str(token.get('user_id')) != str(request.user.pk):
                raise TokenError('Token does not belong to the current user.')
            token.blacklist()
            logger.info("User logged out: %s", request.user.email)
        except TokenError as exc:
            logger.warning(
                "Logout failed for user %s: %s",
                request.user.email,
                str(exc),
            )
            return Response(
                {'detail': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {'detail': 'Successfully logged out.'},
            status=status.HTTP_200_OK,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the current user's profile.

    **GET /auth/me/** — Returns the authenticated user's profile.
    **PATCH /auth/me/** — Updates the authenticated user's profile.

    Permissions: IsAuthenticated
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Return the currently authenticated user."""
        return self.request.user

    def get_serializer_class(self):
        """Use different serializers for read vs. update operations."""
        if self.request.method in ('PUT', 'PATCH'):
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update the user's profile and return the full profile data."""
        partial = kwargs.pop('partial', True)  # Default to partial update
        serializer = self.get_serializer(
            self.get_object(),
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return the full profile using the read serializer
        profile = UserProfileSerializer(self.get_object()).data
        return Response(profile, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    Change the authenticated user's password.

    **POST /auth/change-password/**

    Requires the current password and a new password that meets
    Django's password validation requirements.

    Permissions: IsAuthenticated
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer)
    def post(self, request: Request) -> Response:
        """Validate and change the user's password."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        logger.info("Password changed for user: %s", user.email)

        return Response(
            {'detail': 'Password changed successfully.'},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
    """
    Request a password reset email.

    **POST /auth/password/reset/**

    Always returns 200 OK regardless of whether the email exists,
    to prevent email enumeration attacks.

    Permissions: AllowAny (public endpoint)
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(request=PasswordResetRequestSerializer)
    def post(self, request: Request) -> Response:
        """Send a password reset email (if the account exists)."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        AuthService.send_password_reset_email(email)

        # Always return success to prevent email enumeration
        return Response(
            {
                'detail': (
                    'If an account with this email exists, '
                    'a password reset link has been sent.'
                ),
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """
    Confirm a password reset with token and set new password.

    **POST /auth/password/reset/confirm/**

    Validates the token/uid pair from the reset email and sets the
    new password.

    Permissions: AllowAny (public endpoint — user is identified by token)
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(request=PasswordResetConfirmSerializer)
    def post(self, request: Request) -> Response:
        """Validate the reset token and set the new password."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success = AuthService.reset_password(
            uid=serializer.validated_data['uid'],
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['new_password'],
        )

        if not success:
            return Response(
                {'detail': 'Invalid or expired password reset link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {'detail': 'Password has been reset successfully.'},
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    """
    Confirm an email address from the verification link.

    **POST /auth/verify-email/** ``{"uid": "...", "token": "..."}``

    Permissions: AllowAny (the user is identified by the signed token)
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(request=EmailVerificationSerializer)
    def post(self, request: Request) -> Response:
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not AuthService.verify_email(**serializer.validated_data):
            return Response(
                {'detail': 'Invalid or expired verification link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({'detail': 'Email verified successfully.'})


class ResendVerificationEmailView(APIView):
    """
    Re-send the verification email to the current user.

    **POST /auth/verify-email/resend/**

    Permissions: IsAuthenticated
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(request=None)
    def post(self, request: Request) -> Response:
        if request.user.is_email_verified:
            return Response({'detail': 'Email is already verified.'})
        AuthService.send_verification_email(request.user)
        return Response({'detail': 'Verification email sent.'})


class CustomerPreferenceView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update customer recommendation preferences.

    **GET /auth/preferences/** — Returns the customer's preferences.
    **PATCH /auth/preferences/** — Updates the customer's preferences.

    Preferences are auto-created on first access if they don't exist.
    Only users with the 'customer' role can access this endpoint.

    Permissions: IsAuthenticated + Customer role
    """

    serializer_class = CustomerPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> CustomerPreference:
        """
        Return the customer's preferences, creating them if needed.

        Uses get_or_create to ensure preferences always exist
        when a customer accesses this endpoint.
        """
        preferences, _created = CustomerPreference.objects.get_or_create(
            user=self.request.user,
        )
        return preferences

    def check_permissions(self, request: Request) -> None:
        """Verify the user has the customer role."""
        super().check_permissions(request)
        if request.user.is_authenticated and request.user.role != UserRole.CUSTOMER:
            self.permission_denied(
                request,
                message='Only customers can manage preferences.',
            )

