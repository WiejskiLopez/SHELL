from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class ActionConfig(ValueObject):
    action_type: str
    graph_definition_id: str | None = None
    input_mapping: dict[str, Any] | None = None
    emit_event_type: str | None = None
    emit_event_payload: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.action_type:
            raise ValueError("ActionConfig.action_type cannot be empty")

    def __str__(self) -> str:
        return f"ActionConfig({self.action_type})"
