from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class GraphExecutionStatus(ValueObject, StrEnum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    SUSPENDED = "SUSPENDED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
