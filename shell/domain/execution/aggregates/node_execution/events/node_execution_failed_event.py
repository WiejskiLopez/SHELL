from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt

from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class NodeExecutionFailedEvent(DomainEvent):
    node_id: NodeExecutionId
    role: NodeRole

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self.node_id

    @classmethod
    def now(
        cls,
        node_id: NodeExecutionId,
        now: CreatedAt,
        role: NodeRole | None = None,
    ) -> NodeExecutionFailedEvent:
        return cls(
            occurred_at=now,
            node_id=node_id,
            role=role or NodeRole.AGENT,
        )
