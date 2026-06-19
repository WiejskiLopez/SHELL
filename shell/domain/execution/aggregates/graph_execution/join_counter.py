from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.ids import GraphNodeExecutionId


@dataclass(slots=True)
class JoinCounter:
    transition_id: str
    target_node_execution_id: GraphNodeExecutionId
    wait_count: int
    current_count: int = 0
    completed_source_ids: set[str] = field(default_factory=set)

    @property
    def is_ready(self) -> bool:
        return self.current_count >= self.wait_count

    def record_completion(self, source_node_id: str) -> bool:
        if source_node_id not in self.completed_source_ids:
            self.completed_source_ids.add(source_node_id)
            self.current_count += 1
        return self.is_ready
