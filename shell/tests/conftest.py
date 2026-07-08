"""Root conftest — only global markers and hooks. Zero fixtures."""

from __future__ import annotations

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: fast unit tests, no external dependencies")
    config.addinivalue_line("markers", "integration: tests requiring database or external services")
    config.addinivalue_line("markers", "e2e: end-to-end tests via API or CLI")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("PG_TEST_URL") is None:
        skip_pg = pytest.mark.skip(reason="PG_TEST_URL not set")
        for item in items:
            if "sql_postgres" in str(item.fspath):
                item.add_marker(skip_pg)
