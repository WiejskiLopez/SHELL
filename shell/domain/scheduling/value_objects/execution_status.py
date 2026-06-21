from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class ExecutionStatus(ValueObject, StrEnum):
    PENDING = "pending"
    SKIPPED = "skipped"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
