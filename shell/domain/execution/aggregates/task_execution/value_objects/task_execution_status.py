from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class TaskExecutionStatus(ValueObject, StrEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    EXHAUSTED = "exhausted"
