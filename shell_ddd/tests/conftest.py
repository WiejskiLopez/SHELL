"""Root conftest for shell_ddd tests.

Provides fixtures for all three persistence backends:
- InMemory (always available)
- SQLite (always available)
- PostgreSQL (skipped unless POSTGRES_TEST_URL env var set)
- MongoDB (skipped unless MONGO_TEST_URL env var set)
"""
from __future__ import annotations

import os

import pytest  # noqa: F401 — used in type annotations and fixtures

# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: integration tests requiring external services")
    config.addinivalue_line("markers", "e2e: end-to-end tests")


# ---------------------------------------------------------------------------
# Backend availability flags
# ---------------------------------------------------------------------------

POSTGRES_URL = os.environ.get(
    "POSTGRES_TEST_URL",
    "postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test",
)
MONGO_URL = os.environ.get("MONGO_TEST_URL", "mongodb://localhost:27018/?replicaSet=rs0")

_postgres_available = os.environ.get("POSTGRES_TEST_URL") is not None
_mongo_available = os.environ.get("MONGO_TEST_URL") is not None


# ---------------------------------------------------------------------------
# Skip helpers
# ---------------------------------------------------------------------------

skip_no_postgres = pytest.mark.skipif(
    not _postgres_available,
    reason="POSTGRES_TEST_URL not set — start docker-compose.test.yml to enable",
)

skip_no_mongo = pytest.mark.skipif(
    not _mongo_available,
    reason="MONGO_TEST_URL not set — start docker-compose.test.yml to enable",
)


# ---------------------------------------------------------------------------
# URL fixtures (for integration tests that need raw URLs)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def sqlite_test_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    return f"sqlite+aiosqlite:///{db_path}"


@pytest.fixture(scope="session")
def postgres_test_url() -> str:
    return POSTGRES_URL


@pytest.fixture(scope="session")
def mongo_test_url() -> str:
    return MONGO_URL
