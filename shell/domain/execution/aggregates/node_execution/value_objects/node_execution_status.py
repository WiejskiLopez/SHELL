from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class NodeExecutionStatus(ValueObject, StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
