from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.repositories import (
    GraphDefinitionRepository,
)
from shell.domain.definition.aggregates.graph_definition.value_objects import (
    GraphDefinitionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.definition.value_objects.graph_name import GraphName


class InMemoryGraphDefinitionRepository(
    InMemoryRepository[GraphDefinition, GraphDefinitionId], GraphDefinitionRepository
):
    async def get(self, id: GraphDefinitionId) -> GraphDefinition | None:
        return await self.get_by_id(id)

    async def get_by_id(self, graph_execution_id: GraphDefinitionId) -> GraphDefinition | None:
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
