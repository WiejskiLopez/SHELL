from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class EdgeType(ValueObject, StrEnum):
    SEQUENCE = "SEQUENCE"
    CONDITIONAL = "CONDITIONAL"
    LOOP = "LOOP"
    SPAWN_SUBGRAPH = "SPAWN_SUBGRAPH"
    ERROR_HANDLER = "ERROR_HANDLER"
    TIMEOUT = "TIMEOUT"
    DEFAULT = "DEFAULT"
