from __future__ import annotations

from dataclasses import dataclass

from shell.domain.execution.value_objects.edge_type import EdgeType
from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class TransitionDefinition(ValueObject):
    source_node_execution_id: str
    target_node_execution_id: str | None
    edge_type: EdgeType
    priority: int = 0
    condition_expression: str | None = None
    condition_language: str | None = None
    max_iterations: int = 0
    timeout_seconds: int | None = None
    retry_count: int = 0
    retry_delay_seconds: int = 0
    data_mapping: dict[str, str] | None = None
    label: str = ""

    def __post_init__(self) -> None:
        if self.edge_type == EdgeType.CONDITIONAL and not self.condition_expression:
            raise ValueError("CONDITIONAL transition requires condition_expression")
