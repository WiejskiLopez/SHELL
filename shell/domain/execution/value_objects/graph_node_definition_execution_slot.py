from __future__ import annotations

from dataclasses import dataclass

from shell.domain.execution.aggregates.graph_node_execution.value_objects import (
    GraphNodeExecutionId,
)
from shell.domain.execution.value_objects.graph_node_definition_id import GraphNodeDefinitionId
from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class GraphNodeDefinitionExecutionSlot(ValueObject):
    graph_node_definition_id: GraphNodeDefinitionId
    graph_node_execution_id: GraphNodeExecutionId | None = None

    @property
    def is_filled(self) -> bool:
        return self.graph_node_execution_id is not None

    def with_execution(
        self, execution_id: GraphNodeExecutionId
    ) -> GraphNodeDefinitionExecutionSlot:
        return GraphNodeDefinitionExecutionSlot(
            graph_node_definition_id=self.graph_node_definition_id,
            graph_node_execution_id=execution_id,
        )
