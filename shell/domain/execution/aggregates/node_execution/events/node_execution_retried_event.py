from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.value_objects.node_role import NodeRole
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class NodeExecutionRetriedEvent(DomainEvent):
    node_id: NodeExecutionId
    role: NodeRole

    @classmethod
    def now(
        cls,
        node_id: NodeExecutionId,
        role: NodeRole,
        now: CreatedAt,
    ) -> NodeExecutionRetriedEvent:
        return cls(
            occurred_at=now,
            node_id=node_id,
            role=role,
        )
