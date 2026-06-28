"""Application-level ports — re-exports from granular modules (backward compatibility)."""

from __future__ import annotations

from shell.application.platform.ports.execution import (
    GraphNodeExecutionProcessRunner,
    GraphNodeExecutionWorkspace,
)
from shell.application.platform.ports.filesystem import TaskExecutionLoader
from shell.application.platform.ports.identity import IdGenerator
from shell.application.platform.ports.messaging import EventPublisher
from shell.application.platform.ports.unit_of_work import UnitOfWork
from shell.domain.platform.ports.log import Logger
from shell.domain.platform.ports.time import Clock

__all__ = [
    "Clock",
    "EventPublisher",
    "IdGenerator",
    "Logger",
    "GraphNodeExecutionProcessRunner",
    "GraphNodeExecutionWorkspace",
    "TaskExecutionLoader",
    "UnitOfWork",
]
