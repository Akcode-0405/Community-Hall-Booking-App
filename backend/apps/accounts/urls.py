"""
URL configuration for the accounts app.

All routes are prefixed with ``/api/v1/auth/`` (configured in the root URLconf).

Endpoints:
    POST /register/              — Register a new user
    POST /login/                 — Authenticate and get JWT tokens
    POST /logout/                — Blacklist refresh token
    POST /token/refresh/         — Refresh an access token
    GET  /me/                    — Get current user profile
    PATCH /me/                   — Update current user profile
    POST /change-password/       — Change authenticated user's password
    POST /password/reset/        — Request password reset email
    POST /password/reset/confirm/ — Confirm password reset with token
    POST /verify-email/          — Confirm email with uid/token
    POST /verify-email/resend/   — Re-send the verification email
    GET  /preferences/           — Get customer preferences
    PATCH /preferences/          — Update customer preferences
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'accounts'

urlpatterns = [
    # Registration & authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Profile management
    path('me/', views.UserProfileView.as_view(), name='profile'),

    # Password management
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('password/reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path(
        'password/reset/confirm/',
        views.PasswordResetConfirmView.as_view(),
        name='password-reset-confirm',
    ),

    # Email verification
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path(
        'verify-email/resend/',
        views.ResendVerificationEmailView.as_view(),
        name='verify-email-resend',
    ),

    # Customer preferences
    path('preferences/', views.CustomerPreferenceView.as_view(), name='customer-preferences'),
]

