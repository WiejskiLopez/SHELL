from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class ExecutionStatus(ValueObject, StrEnum):
    PENDING = "PENDING"
    SKIPPED = "SKIPPED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
