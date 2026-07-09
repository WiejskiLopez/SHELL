from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class GraphExecutionStatus(ValueObject, StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
