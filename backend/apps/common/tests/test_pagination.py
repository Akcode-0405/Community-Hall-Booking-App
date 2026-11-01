"""
Tests for apps.common pagination classes.
"""
from __future__ import annotations

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.common.pagination import (
    LargeResultsSetPagination,
    SmallResultsSetPagination,
    StandardResultsSetPagination,
)


class TestPagination:
    """Test custom pagination classes."""

    def test_standard_pagination(self):
        paginator = StandardResultsSetPagination()
        factory = APIRequestFactory()
        wsgi_request = factory.get("/test/?page=1&page_size=10")
        drf_request = Request(wsgi_request)

        items = list(range(25))
        page = paginator.paginate_queryset(items, drf_request)
        response = paginator.get_paginated_response(page)

        assert response.data["count"] == 25
        assert response.data["total_pages"] == 3
        assert len(response.data["results"]) == 10
        assert response.data["next"] is not None
        assert response.data["previous"] is None

    def test_large_pagination_default_size(self):
        paginator = LargeResultsSetPagination()
        assert paginator.page_size == 50
        assert paginator.max_page_size == 100

    def test_small_pagination_default_size(self):
        paginator = SmallResultsSetPagination()
        assert paginator.page_size == 10
        assert paginator.max_page_size == 100
