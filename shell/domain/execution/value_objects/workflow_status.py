from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class WorkflowStatus(ValueObject, StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABORTED = "aborted"
