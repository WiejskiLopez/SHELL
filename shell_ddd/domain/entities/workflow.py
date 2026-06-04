"""Workflow aggregate with embedded NodeStates."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import NodeId, WorkflowId


@dataclass(slots=True)
class NodeState:
    node_id: NodeId
    status: Status
    step: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


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
        now: datetime | None = None,
    ) -> Workflow:
        created = now or datetime.now(tz=UTC)
        return cls(
            id=id_,
            task_name=task_name,
            status=Status.idle(),
            created_at=created,
        )

    def start(self, now: datetime | None = None) -> None:
        self.status = Status.running()

    def complete(self) -> None:
        self.status = Status.done()

    def fail(self) -> None:
        self.status = Status.failed()

    def update_node_state(self, node_id: NodeId, status: Status, step: int = 0) -> None:
        self.node_states[node_id.value] = NodeState(
            node_id=node_id,
            status=status,
            step=step,
        )
