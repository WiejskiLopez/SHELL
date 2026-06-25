from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class GraphExecutionStatus(ValueObject, StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    SPAWNING = "spawning"
    READY = "ready"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
