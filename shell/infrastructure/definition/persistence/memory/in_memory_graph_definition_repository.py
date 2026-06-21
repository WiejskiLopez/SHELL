from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.repositories.graph_definition_repository import GraphDefinitionRepository
from shell.domain.definition.value_objects.ids import GraphDefinitionId

if TYPE_CHECKING:
    from shell.domain.definition.entities.graph_definition import GraphDefinition


class InMemoryGraphDefinitionRepository(GraphDefinitionRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphDefinition] = {}

    async def get(self, graph_execution_id: GraphDefinitionId) -> GraphDefinition | None:
        return self._store.get(graph_execution_id.value)

    async def get_graph_definition_by_name(self, graph_definition_by_name: str) -> GraphDefinition | None:
        for graph_definition in self._store.values():
            if graph_definition.name == graph_definition_by_name:
                return graph_definition
        return None

    async def get_by_id(self, id_: GraphDefinitionId) -> GraphDefinition | None:
        return self._store.get(id_.value)

    async def save(self, graph: GraphDefinition) -> None:
        self._store[graph.id.value] = graph

    async def list_all(self) -> list[GraphDefinition]:
        return list(self._store.values())
