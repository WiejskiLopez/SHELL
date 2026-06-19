from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.value_objects.ids import GraphNodeExecutionId


@dataclass(slots=True)
class ParallelGroup:
    group_id: str
    fork_node_execution_id: GraphNodeExecutionId
    pending_node_ids: set[str] = field(default_factory=set)
    completed_node_ids: set[str] = field(default_factory=set)

    @property
    def is_complete(self) -> bool:
        return len(self.pending_node_ids) == 0 and len(self.completed_node_ids) > 0

    def mark_completed(self, node_id: str) -> None:
        self.pending_node_ids.discard(node_id)
        self.completed_node_ids.add(node_id)
