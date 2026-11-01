"""
DRF throttle classes for the Hall Booking SaaS Platform.

Provides three throttle tiers:

- **BurstRateThrottle**: 60 requests/minute — protects against short bursts.
- **SustainedRateThrottle**: 1000 requests/day — limits sustained abuse.
- **AuthRateThrottle**: 5 requests/minute — protects authentication endpoints.

Configure in DRF settings::

    REST_FRAMEWORK = {
        'DEFAULT_THROTTLE_CLASSES': [
            'apps.common.throttling.BurstRateThrottle',
            'apps.common.throttling.SustainedRateThrottle',
        ],
    }

Or per-view::

    class LoginView(TokenObtainPairView):
        throttle_classes = [AuthRateThrottle]
"""

from __future__ import annotations

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """
    Throttle for short bursts: 60 requests per minute.

    Applied globally to authenticated users to prevent rapid-fire
    requests that could overload the API or indicate a runaway client.

    Scope: ``burst``

    Settings::

        REST_FRAMEWORK = {
            'DEFAULT_THROTTLE_RATES': {
                'burst': '60/min',
            },
        }
    """

    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    """
    Throttle for sustained usage: 1000 requests per day.

    Applied globally to authenticated users to enforce daily usage
    limits and prevent abuse.

    Scope: ``sustained``

    Settings::

        REST_FRAMEWORK = {
            'DEFAULT_THROTTLE_RATES': {
                'sustained': '1000/day',
            },
        }
    """

    scope = "sustained"


class AuthRateThrottle(AnonRateThrottle):
    """
    Throttle for authentication endpoints: 5 requests per minute.

    Applied to login, registration, and password reset views to mitigate
    brute-force attacks and credential stuffing.  Uses anonymous rate
    throttling (keyed by IP) since the user hasn't authenticated yet.

    Scope: ``auth``

    Settings::

        REST_FRAMEWORK = {
            'DEFAULT_THROTTLE_RATES': {
                'auth': '5/min',
            },
        }

    Example::

        class LoginView(TokenObtainPairView):
            throttle_classes = [AuthRateThrottle]
    """

    scope = "auth"
