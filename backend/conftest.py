"""
Root conftest for pytest fixtures shared across all test modules.

This file is automatically loaded by pytest and provides common fixtures
used throughout the test suite, such as API clients and authenticated users.
"""
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    """Return an unauthenticated DRF API test client.

    Usage in tests:
        def test_example(api_client):
            response = api_client.get('/api/v1/some-endpoint/')
            assert response.status_code == 200
    """
    return APIClient()
