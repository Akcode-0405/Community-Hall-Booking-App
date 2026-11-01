"""
Tests for apps.common middleware classes.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.http import HttpResponse

from apps.accounts.models import UserRole
from apps.common.middleware import AuditLogMiddleware, TenantMiddleware


class TestMiddleware:
    """Test suite for custom middleware."""

    def test_tenant_middleware_attaches_none_for_anonymous(self):
        request = MagicMock()
        request.user = MagicMock(is_authenticated=False)

        get_response = MagicMock(return_value=HttpResponse("OK"))
        middleware = TenantMiddleware(get_response)

        response = middleware(request)
        assert response.status_code == 200
        assert getattr(request, "tenant", None) is None
        assert getattr(request, "tenant_membership", None) is None

    @patch("apps.common.middleware.audit_logger")
    def test_audit_log_middleware_logs_write_operations(self, mock_audit_logger):
        request = MagicMock()
        request.method = "POST"
        request.path = "/api/v1/auth/register/"
        request.user = MagicMock(is_authenticated=True, pk="user-123", role=UserRole.CUSTOMER)
        request.tenant = None
        request.META = {"REMOTE_ADDR": "127.0.0.1"}

        get_response = MagicMock(return_value=HttpResponse("Created", status=201))
        middleware = AuditLogMiddleware(get_response)

        response = middleware(request)

        assert response.status_code == 201
        assert mock_audit_logger.info.called
        log_msg = mock_audit_logger.info.call_args[0][0]
        assert "AUDIT | method=%s path=%s status=%s" in log_msg

    @patch("apps.common.middleware.audit_logger")
    def test_audit_log_middleware_ignores_safe_methods(self, mock_audit_logger):
        request = MagicMock()
        request.method = "GET"
        request.path = "/api/v1/auth/me/"

        get_response = MagicMock(return_value=HttpResponse("OK", status=200))
        middleware = AuditLogMiddleware(get_response)

        response = middleware(request)

        assert response.status_code == 200
        assert not mock_audit_logger.info.called
