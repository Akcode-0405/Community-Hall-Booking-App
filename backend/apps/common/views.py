"""Operational endpoints shared by the whole platform."""

from __future__ import annotations

from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Liveness/readiness probe used by Docker and load balancers.

    **GET /api/health/** → ``{"status": "ok"}`` when the database answers.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    throttle_classes: list = []

    @extend_schema(exclude=True)
    def get(self, request: Request) -> Response:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return Response({"status": "ok"})
