from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class GraphNodeExecutionStatus(ValueObject, StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
