from __future__ import annotations

import warnings
from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject

warnings.warn(
    "TransitionType is deprecated — use EdgeType from shell.domain.execution.value_objects.edge_type instead.",
    DeprecationWarning,
    stacklevel=2,
)


class TransitionType(ValueObject, StrEnum):
    SEQUENCE = "sequence"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"
    JOIN = "join"
    ERROR_HANDLER = "error_handler"
    LOOP = "loop"
    TIMEOUT = "timeout"
    DEFAULT = "default"
