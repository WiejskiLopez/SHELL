from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class TaskExecutionStatus(ValueObject, StrEnum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    EXHAUSTED = "EXHAUSTED"
