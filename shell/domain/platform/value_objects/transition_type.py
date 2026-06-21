from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class TransitionType(ValueObject, StrEnum):
    SEQUENCE = "sequence"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"
    JOIN = "join"
    ERROR_HANDLER = "error_handler"
    LOOP = "loop"
    TIMEOUT = "timeout"
    DEFAULT = "default"
