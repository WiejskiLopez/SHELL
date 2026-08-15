from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class WorkflowStatus(ValueObject, StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
