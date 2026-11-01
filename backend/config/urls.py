"""
URL configuration for the Hall Booking SaaS Platform.

Routes:
    /admin/          — Django admin interface
    /api/v1/auth/    — Authentication & user management endpoints
    /api/v1/tenants/ — Tenant organisations, members, invitations
    /api/v1/subscriptions/ — SaaS plans, subscriptions, invoices
    /api/v1/payments/      — Razorpay payment verification & webhooks
    /api/health/     — Health probe
    /api/schema/     — OpenAPI 3.0 schema (JSON/YAML)
    /api/docs/       — Swagger UI interactive documentation
    /api/redoc/      — ReDoc documentation (alternative viewer)

Debug-only routes:
    /media/          — Serve user-uploaded media files (dev only)
    /__debug__/      — Django Debug Toolbar (dev only)
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.common.views import HealthCheckView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # -------------------------------------------------------------------------
    # API v1 endpoints
    # -------------------------------------------------------------------------
    path('api/v1/auth/', include('apps.accounts.urls')),
    # Phase 2 (in progress):
    # path('api/v1/tenants/', include('apps.tenants.urls')),
    # path('api/v1/subscriptions/', include('apps.subscriptions.urls')),
    # path('api/v1/payments/', include('apps.payments.urls')),

    # Health probe (Docker / load balancer)
    path('api/health/', HealthCheckView.as_view(), name='health'),

    # -------------------------------------------------------------------------
    # API Documentation (OpenAPI 3.0)
    # -------------------------------------------------------------------------
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
]

# Serve media files in development (Django's dev server only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Enable Django Debug Toolbar if installed
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
