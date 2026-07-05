from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
        NodeDefinitionId,
    )
    from shell.domain.definition.value_objects.node_position import NodePosition
    from shell.domain.definition.value_objects.node_role_name import NodeRoleName
    from shell.domain.definition.value_objects.node_type_name import NodeTypeName
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class NodeDefinitionCreatedEvent(DomainEvent):
    node_definition_id: NodeDefinitionId
    position: NodePosition
    role: NodeRoleName
    node_type: NodeTypeName

    @classmethod
    def now(
        cls,
        node_definition_id: NodeDefinitionId,
        position: NodePosition,
        role: NodeRoleName,
        node_type: NodeTypeName,
        now: CreatedAt,
    ) -> NodeDefinitionCreatedEvent:
        return cls(
            occurred_at=now,
            node_definition_id=node_definition_id,
            position=position,
            role=role,
            node_type=node_type,
        )
