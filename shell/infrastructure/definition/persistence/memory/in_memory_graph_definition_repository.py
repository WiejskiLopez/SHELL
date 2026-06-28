from __future__ import annotations

from shell.domain.definition.repositories.graph_definition_repository import (
    GraphDefinitionRepository,
)
from shell.domain.definition.value_objects.graph_name import GraphName
from shell.domain.definition.value_objects.ids import (
    GraphDefinitionId,
)
from shell.domain.definition.entities.graph_definition import GraphDefinition
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryGraphDefinitionRepository(InMemoryRepository[GraphDefinition, GraphDefinitionId], GraphDefinitionRepository):

    async def get(self, graph_execution_id: GraphDefinitionId) -> GraphDefinition | None:
        return self._store.get(graph_execution_id.value)

    async def get_graph_definition_by_name(
        self, graph_definition_by_name: GraphName
    ) -> GraphDefinition | None:
        for graph_definition in self._store.values():
            if graph_definition.name == graph_definition_by_name:
                return graph_definition
        return None

    async def list_all(self) -> list[GraphDefinition]:
        return list(self._store.values())
