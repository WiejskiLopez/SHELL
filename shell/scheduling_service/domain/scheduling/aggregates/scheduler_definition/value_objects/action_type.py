from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class ActionType(ValueObject, StrEnum):
    SPAWN_GRAPH = "spawn_graph"
    RELAY = "relay"
    CLEANUP = "cleanup"
    MONITOR = "monitor"
