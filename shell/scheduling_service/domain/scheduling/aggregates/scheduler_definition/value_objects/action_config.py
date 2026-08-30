from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.base.value_object import ValueObject

if TYPE_CHECKING:
    from shell.platform.types import JsonStr
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.action_type import (
        ActionType,
    )


@dataclass(frozen=True, slots=True)
class ActionConfig(ValueObject):
    action_type: ActionType
    graph_definition_id: str | None = None
    input_mapping: JsonStr | None = None
    emit_event_type: str | None = None
    emit_event_payload: JsonStr | None = None

    def __str__(self) -> str:
        return f"ActionConfig({self.action_type})"
