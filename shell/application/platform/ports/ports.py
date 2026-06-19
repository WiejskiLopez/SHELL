"""Application-level ports — re-exports from granular modules (backward compatibility)."""

from __future__ import annotations

from shell.application.platform.ports.execution import NodeProcessRunner, NodeWorkspace
from shell.application.platform.ports.filesystem import TaskExecutionLoader
from shell.application.platform.ports.identity import IdGenerator
from shell.application.platform.ports.logging import Logger
from shell.application.platform.ports.messaging import EventPublisher
from shell.application.platform.ports.time import Clock
from shell.application.platform.ports.unit_of_work import UnitOfWork

__all__ = [
    "Clock",
    "EventPublisher",
    "IdGenerator",
    "Logger",
    "NodeProcessRunner",
    "NodeWorkspace",
    "TaskExecutionLoader",
    "UnitOfWork",
]
