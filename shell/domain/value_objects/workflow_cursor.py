"""WorkflowCursor — pointer to the node currently being executed.

A WorkflowCursor encapsulates ``current_graph_node_execution_id`` so the Workflow aggregate
does not leak a bare ``str | None`` to the rest of the system. It is also the
extension seam for future multi-cursor scenarios (parallel branches).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.value_objects.ids import GraphNodeExecutionId


@dataclass(frozen=True, slots=True)
class WorkflowCursor:
    """Immutable VO pointing to the node currently scheduled for execution."""

    current_graph_node_execution_id: GraphNodeExecutionId | None = None

    @classmethod
    def empty(cls) -> WorkflowCursor:
        return cls(current_graph_node_execution_id=None)

    @classmethod
    def at(cls, graph_node_execution_id: GraphNodeExecutionId) -> WorkflowCursor:
        return cls(current_graph_node_execution_id=graph_node_execution_id)

    def is_active(self) -> bool:
        return self.current_graph_node_execution_id is not None

    def points_to(self, graph_node_execution_id: GraphNodeExecutionId) -> bool:
        return (
            self.current_graph_node_execution_id is not None
            and self.current_graph_node_execution_id == graph_node_execution_id
        )

    def cleared(self) -> WorkflowCursor:
        return WorkflowCursor(current_graph_node_execution_id=None)
