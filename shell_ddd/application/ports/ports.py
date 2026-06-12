"""Application-level ports — re-exports from granular modules (backward compatibility)."""
from __future__ import annotations

from shell_ddd.application.ports.execution import NodeProcessRunner, NodeWorkspace
from shell_ddd.application.ports.filesystem import TaskLoader
from shell_ddd.application.ports.identity import IdGenerator
from shell_ddd.application.ports.logging import Logger
from shell_ddd.application.ports.messaging import EventPublisher
from shell_ddd.application.ports.time import Clock
from shell_ddd.application.ports.unit_of_work import UnitOfWork

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