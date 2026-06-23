from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class GraphNodeExecutionStatus(ValueObject, StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
