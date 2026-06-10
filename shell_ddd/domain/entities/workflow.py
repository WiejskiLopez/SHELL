"""Workflow aggregate with embedded NodeStates."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import NodeId, NodeStateId, WorkflowId


@dataclass(slots=True)
class NodeState:
    id: NodeStateId
    node_id: NodeId
    status: Status
    updated_at: datetime
    step: int = 0


@dataclass(slots=True)
class Workflow:
    """Workflow aggregate root."""

    id: WorkflowId
    task_name: str
    status: Status
    created_at: datetime
    node_states: dict[str, NodeState] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        *,
        id_: WorkflowId,
        task_name: str,
        now: datetime,
    ) -> Workflow:
        return cls(
            id=id_,
            task_name=task_name,
            status=Status.idle(),
            created_at=now,
        )

    def start(self, now: datetime) -> None:
        self.status = Status.running()

    def complete(self) -> None:
        self.status = Status.done()

    def fail(self) -> None:
        self.status = Status.failed()

    def update_node_state(self, node_id: NodeId, status: Status, now: datetime, step: int = 0) -> None:
        from shell_ddd.domain.value_objects.ids import NodeStateId

        existing = self.node_states.get(node_id.value)
        state_id = existing.id if existing else NodeStateId.generate()
        self.node_states[node_id.value] = NodeState(
            id=state_id,
            node_id=node_id,
            status=status,
            updated_at=now,
            step=step,
        )
