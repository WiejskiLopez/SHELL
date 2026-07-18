from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.base.value_object import ValueObject

if TYPE_CHECKING:
    from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class ActionConfig(ValueObject):
    action_type: str
    graph_definition_id: str | None = None
    input_mapping: JsonStr | None = None
    emit_event_type: str | None = None
    emit_event_payload: JsonStr | None = None

    def __post_init__(self) -> None:
        if not self.action_type:
            raise DomainError("ActionConfig.action_type cannot be empty")

    def __str__(self) -> str:
        return f"ActionConfig({self.action_type})"
