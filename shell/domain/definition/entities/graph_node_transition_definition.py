from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.value_objects.transition_type import TransitionType

if TYPE_CHECKING:
    from shell.domain.definition.value_objects.ids import (
    GraphDefinitionId,
    GraphNodeDefinitionId,
    GraphNodeTransitionDefinitionId
)


@dataclass(slots=True)
class GraphNodeTransitionDefinition:
    id: GraphNodeTransitionDefinitionId
    graph_definition_id: GraphDefinitionId
    source_node_definition_id: GraphNodeDefinitionId | None
    target_node_definition_id: GraphNodeDefinitionId
    transition_type: TransitionType
    priority: int = 0
    condition_expression: str | None = None
    condition_language: str | None = None
    max_loop_count: int = 0
    timeout_seconds: int | None = None
    retry_count: int = 0
    retry_delay_seconds: int = 0
    data_mapping: dict[str, str] | None = None
    label: str = ""

    def __post_init__(self) -> None:
        if self.transition_type == TransitionType.CONDITIONAL and not self.condition_expression:
            raise ValueError("CONDITIONAL transition requires condition_expression")
