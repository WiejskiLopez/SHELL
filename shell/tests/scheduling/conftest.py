"""Scheduling BC test fixtures."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shell.platform.infrastructure.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    InMemoryUnitOfWork,
)


@pytest.fixture()
def unit_of_work() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock(datetime(2024, 1, 1, tzinfo=UTC))


@pytest.fixture()
def id_generator() -> FakeIdGenerator:
    return FakeIdGenerator()
