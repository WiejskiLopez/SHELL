from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class GraphExecutionInitializationStatus(ValueObject, StrEnum):
    PENDING = "pending"
    INITIALIZING = "initializing"
    COMPLETED = "completed"
    HOLD = "hold"
    FAILED = "failed"
