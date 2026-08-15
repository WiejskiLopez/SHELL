"""Scheduling BC test fixtures."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shell.platform.infrastructure.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
)
from shell.scheduling.infrastructure.scheduling.persistence.memory.unit_of_work import (
    InMemorySchedulingUnitOfWork,
)


@pytest.fixture()
def unit_of_work() -> InMemorySchedulingUnitOfWork:
    return InMemorySchedulingUnitOfWork()


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock(datetime(2024, 1, 1, tzinfo=UTC))


@pytest.fixture()
def id_generator() -> FakeIdGenerator:
    return FakeIdGenerator()
