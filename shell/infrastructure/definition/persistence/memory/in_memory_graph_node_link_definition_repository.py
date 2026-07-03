from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_node_link_definition.graph_node_link_definition import (
    GraphNodeLinkDefinition,
)
from shell.domain.definition.aggregates.graph_node_link_definition.value_objects.graph_node_link_definition_id import (
    GraphNodeLinkDefinitionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class InMemoryGraphNodeLinkDefinitionRepository(
    InMemoryRepository[GraphNodeLinkDefinition, GraphNodeLinkDefinitionId],
):
    async def get_by_id(
        self,
        graph_node_link_definition_id: GraphNodeLinkDefinitionId,
    ) -> GraphNodeLinkDefinition | None:
        return self._store.get(graph_node_link_definition_id.value)

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[GraphNodeLinkDefinition]:
        return [
            link
            for link in self._store.values()
            if link.graph_definition_id == graph_definition_id
        ]

    async def list_by_graph_node_definition_id(
        self,
        graph_node_definition_id: GraphNodeDefinitionId,
    ) -> list[GraphNodeLinkDefinition]:
        return [
            link
            for link in self._store.values()
            if link.graph_node_definition_id == graph_node_definition_id
        ]

    async def save(self, link: GraphNodeLinkDefinition) -> None:
        self._store[link.id.value] = link

    async def delete(self, id: GraphNodeLinkDefinitionId) -> None:
        self._store.pop(id.value, None)

    async def exists(self, id: GraphNodeLinkDefinitionId) -> ExistsResult:
        return ExistsResult(id.value in self._store)
