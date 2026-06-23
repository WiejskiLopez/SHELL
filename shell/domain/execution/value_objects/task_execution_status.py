from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class TaskExecutionStatus(ValueObject, StrEnum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXHAUSTED = "EXHAUSTED"
