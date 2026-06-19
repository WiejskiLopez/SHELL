from __future__ import annotations

from enum import StrEnum


class TransitionType(StrEnum):
    SEQUENCE = "sequence"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"
    JOIN = "join"
    ERROR_HANDLER = "error_handler"
    LOOP = "loop"
    TIMEOUT = "timeout"
    DEFAULT = "default"
