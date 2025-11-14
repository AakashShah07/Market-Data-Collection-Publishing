"""Fixtures for pytest."""

import pytest
from fastapi.testclient import TestClient
from respx import MockRouter

from app.main import app


@pytest.fixture(scope="module")
def test_client() -> TestClient:
    """Returns a TestClient instance for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def respx_mock() -> MockRouter:
    """Returns a MockRouter instance for mocking HTTPX requests."""
    with MockRouter() as mock:
        yield mock
