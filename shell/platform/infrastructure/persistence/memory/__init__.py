"""Platformowe InMemory persistence adapters — tylko platformowe fake'i."""

from __future__ import annotations

import logging

from shell.platform.infrastructure.persistence.memory.fake_clock import FakeClock
from shell.platform.infrastructure.persistence.memory.fake_event_publisher import FakeEventPublisher
from shell.platform.infrastructure.persistence.memory.fake_id_generator import FakeIdGenerator
from shell.platform.infrastructure.persistence.memory.fake_logger import FakeLogger
from shell.platform.infrastructure.persistence.memory.fake_task_loader import FakeTaskLoader
from shell.platform.infrastructure.persistence.memory.in_memory_saga_repository import (
    InMemorySagaRepository,
)

logger = logging.getLogger(__name__)

__all__ = [
    "FakeClock",
    "FakeEventPublisher",
    "FakeIdGenerator",
    "FakeLogger",
    "FakeTaskLoader",
    "InMemorySagaRepository",
]
