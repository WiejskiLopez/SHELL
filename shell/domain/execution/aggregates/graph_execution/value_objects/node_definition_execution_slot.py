from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.base.value_object import ValueObject

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_definition_id import (
        NodeDefinitionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )


@dataclass(frozen=True, slots=True)
class NodeDefinitionExecutionSlot(ValueObject):
    node_definition_id: NodeDefinitionId
    node_execution_id: NodeExecutionId | None = None

    @property
    def is_filled(self) -> bool:
        return self.node_execution_id is not None

    def with_execution(self, execution_id: NodeExecutionId) -> NodeDefinitionExecutionSlot:
        return NodeDefinitionExecutionSlot(
            node_definition_id=self.node_definition_id,
            node_execution_id=execution_id,
        )
