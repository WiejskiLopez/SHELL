"""Platform test fixtures — only platform-specific infrastructure."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from shell.platform.infrastructure.logging.stdlib_logger import correlation_id_var
from shell.platform.infrastructure.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
)
from shell.tests.shared.test_db import build_db_url as test_db_url


@pytest.fixture(scope="session")
def sqlite_test_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    return test_db_url(tmp_path_factory, subdir="db", db_name="test.db")


@pytest.fixture(autouse=True)
def auto_correlation_id():
    token = correlation_id_var.set(f"test-{uuid.uuid4()}")
    yield
    correlation_id_var.reset(token)


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock(datetime(2024, 1, 1, tzinfo=UTC))


@pytest.fixture()
def id_generator() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def task_execution_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# SQL Task")


@pytest.fixture()
def fake_logger() -> FakeLogger:
    return FakeLogger()
