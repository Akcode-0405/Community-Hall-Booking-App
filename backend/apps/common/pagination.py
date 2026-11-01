"""
DRF pagination classes for the Hall Booking SaaS Platform.

Three page-size presets cover most use cases:

- **StandardResultsSetPagination** (20/page): Default for most list endpoints.
- **LargeResultsSetPagination** (50/page): For admin dashboards and exports.
- **SmallResultsSetPagination** (10/page): For mobile or card-based UIs.

All classes include ``total_count`` and ``total_pages`` in the response
for easier frontend pagination rendering.
"""

from __future__ import annotations

import math
from collections import OrderedDict
from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Default pagination: 20 items per page, max 100.

    Query parameters:
        - ``page``: Page number (1-indexed).
        - ``page_size``: Items per page (overrides default, capped at max).

    Response metadata:
        - ``count``: Total number of items.
        - ``total_pages``: Total number of pages.
        - ``next``: URL for the next page (or null).
        - ``previous``: URL for the previous page (or null).
        - ``results``: List of items.

    Example::

        class HallListView(generics.ListAPIView):
            pagination_class = StandardResultsSetPagination
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data: list[Any]) -> Response:
        """Return paginated response with total_count and total_pages."""
        total_count = self.page.paginator.count
        page_size = self.get_page_size(self.request)
        total_pages = math.ceil(total_count / page_size) if page_size else 0

        return Response(
            OrderedDict(
                [
                    ("count", total_count),
                    ("total_pages", total_pages),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )

    def get_paginated_response_schema(self, schema: dict) -> dict:
        """Provide OpenAPI schema for the paginated response."""
        return {
            "type": "object",
            "required": ["count", "total_pages", "results"],
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Total number of items.",
                    "example": 42,
                },
                "total_pages": {
                    "type": "integer",
                    "description": "Total number of pages.",
                    "example": 3,
                },
                "next": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "description": "URL of the next page.",
                },
                "previous": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "description": "URL of the previous page.",
                },
                "results": schema,
            },
        }


class LargeResultsSetPagination(StandardResultsSetPagination):
    """
    Large-page pagination: 50 items per page, max 100.

    Suitable for admin dashboards, data export previews, and bulk
    listing screens.
    """

    page_size = 50


class SmallResultsSetPagination(StandardResultsSetPagination):
    """
    Small-page pagination: 10 items per page, max 100.

    Suitable for mobile interfaces, card-based layouts, and search
    results where fewer items per page improve UX.
    """

    page_size = 10
