from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_node_transition_definition.graph_node_transition_definition import (
    GraphNodeTransitionDefinition,
)
from shell.domain.definition.aggregates.graph_node_transition_definition.repositories import (
    GraphNodeTransitionDefinitionRepository,
)
from shell.domain.definition.aggregates.graph_node_transition_definition.value_objects import (
    GraphNodeTransitionDefinitionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )


class InMemoryGraphNodeTransitionDefinitionRepository(
    InMemoryRepository[GraphNodeTransitionDefinition, GraphNodeTransitionDefinitionId],
    GraphNodeTransitionDefinitionRepository,
):
    async def save(self, transition: GraphNodeTransitionDefinition) -> None:
        self._store[transition.id.value] = transition

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[GraphNodeTransitionDefinition]:
        return [t for t in self._store.values() if t.graph_definition_id == graph_definition_id]
