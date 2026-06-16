"""WorkflowCursor — pointer to the node currently being executed.

A WorkflowCursor encapsulates ``current_node_id`` so the Workflow aggregate
does not leak a bare ``str | None`` to the rest of the system. It is also the
extension seam for future multi-cursor scenarios (parallel branches).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.value_objects.ids import NodeId


@dataclass(frozen=True, slots=True)
class WorkflowCursor:
    """Immutable VO pointing to the node currently scheduled for execution."""

    current_node_id: NodeId | None = None

    @classmethod
    def empty(cls) -> WorkflowCursor:
        return cls(current_node_id=None)

    @classmethod
    def at(cls, node_id: NodeId) -> WorkflowCursor:
        return cls(current_node_id=node_id)

    def is_active(self) -> bool:
        return self.current_node_id is not None

    def points_to(self, node_id: NodeId) -> bool:
        return self.current_node_id is not None and self.current_node_id == node_id

    def cleared(self) -> WorkflowCursor:
        return WorkflowCursor(current_node_id=None)
