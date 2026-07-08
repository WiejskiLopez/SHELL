"""Platformowe InMemory persistence adapters — tylko platformowe fake'i."""

from __future__ import annotations

import logging

from shell.infrastructure.platform.persistence.memory.fake_clock import FakeClock
from shell.infrastructure.platform.persistence.memory.fake_event_publisher import FakeEventPublisher
from shell.infrastructure.platform.persistence.memory.fake_id_generator import FakeIdGenerator
from shell.infrastructure.platform.persistence.memory.fake_logger import FakeLogger
from shell.infrastructure.platform.persistence.memory.fake_task_loader import FakeTaskLoader
from shell.infrastructure.platform.persistence.memory.in_memory_query_services import (
    InMemoryQueryServices,
)
from shell.infrastructure.platform.persistence.memory.in_memory_unit_of_work import (
    InMemoryUnitOfWork,
)

logger = logging.getLogger(__name__)

__all__ = [
    "FakeClock",
    "FakeEventPublisher",
    "FakeIdGenerator",
    "FakeLogger",
    "FakeTaskLoader",
    "InMemoryQueryServices",
    "InMemoryUnitOfWork",
]
