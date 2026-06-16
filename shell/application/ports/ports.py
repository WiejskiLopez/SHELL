"""Application-level ports — re-exports from granular modules (backward compatibility)."""

from __future__ import annotations

from shell.application.ports.execution import NodeProcessRunner, NodeWorkspace
from shell.application.ports.filesystem import TaskLoader
from shell.application.ports.identity import IdGenerator
from shell.application.ports.logging import Logger
from shell.application.ports.messaging import EventPublisher
from shell.application.ports.time import Clock
from shell.application.ports.unit_of_work import UnitOfWork

__all__ = [
    "Clock",
    "EventPublisher",
    "IdGenerator",
    "Logger",
    "NodeProcessRunner",
    "NodeWorkspace",
    "TaskLoader",
    "UnitOfWork",
]
