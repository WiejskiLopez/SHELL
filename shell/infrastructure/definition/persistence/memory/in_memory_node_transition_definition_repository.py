from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.node_transition_definition.node_transition_definition import (
    NodeTransitionDefinition,
)
from shell.domain.definition.aggregates.node_transition_definition.repositories import (
    NodeTransitionDefinitionRepository,
)
from shell.domain.definition.aggregates.node_transition_definition.value_objects import (
    NodeTransitionDefinitionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )


class InMemoryNodeTransitionDefinitionRepository(
    InMemoryRepository[NodeTransitionDefinition, NodeTransitionDefinitionId],
    NodeTransitionDefinitionRepository,
):
    async def save(self, transition: NodeTransitionDefinition) -> None:
        self._store[transition.id.value] = transition

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[NodeTransitionDefinition]:
        return [t for t in self._store.values() if t.graph_definition_id == graph_definition_id]
