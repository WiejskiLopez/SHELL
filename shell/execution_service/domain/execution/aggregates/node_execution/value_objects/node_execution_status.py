from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class NodeExecutionStatus(ValueObject, StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
