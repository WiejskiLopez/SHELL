"""Platformowe InMemory persistence adapters — tylko platformowe fake'i."""

from __future__ import annotations

import logging

from shell.platform.infrastructure.persistence.memory.fake_clock import FakeClock
from shell.platform.infrastructure.persistence.memory.fake_event_publisher import FakeEventPublisher
from shell.platform.infrastructure.persistence.memory.fake_id_generator import FakeIdGenerator
from shell.platform.infrastructure.persistence.memory.fake_logger import FakeLogger
from shell.platform.infrastructure.persistence.memory.fake_message_publisher import (
    FakeMessagePublisher,
)
from shell.platform.infrastructure.persistence.memory.fake_task_loader import FakeTaskLoader

logger = logging.getLogger(__name__)

__all__ = [
    "FakeClock",
    "FakeEventPublisher",
    "FakeIdGenerator",
    "FakeLogger",
    "FakeMessagePublisher",
    "FakeTaskLoader",
]
