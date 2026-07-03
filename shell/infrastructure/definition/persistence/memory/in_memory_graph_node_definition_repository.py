from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_node_definition.graph_node_definition import (
    GraphNodeDefinition,
)
from shell.domain.definition.aggregates.graph_node_definition.repositories import (
    GraphNodeDefinitionRepository,
)
from shell.domain.definition.aggregates.graph_node_definition.value_objects import (
    GraphNodeDefinitionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects import (
        GraphDefinitionId,
    )
    from shell.infrastructure.definition.persistence.memory.in_memory_graph_node_link_definition_repository import (
        InMemoryGraphNodeLinkDefinitionRepository,
    )


class InMemoryGraphNodeDefinitionRepository(
    InMemoryRepository[GraphNodeDefinition, GraphNodeDefinitionId], GraphNodeDefinitionRepository
):
    def __init__(self) -> None:
        super().__init__()
        self._link_repo: object = None

    def set_link_repo(self, link_repo: object) -> None:
        self._link_repo = link_repo

    async def save(self, node: GraphNodeDefinition) -> None:
        self._store[node.id.value] = node

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[GraphNodeDefinition]:
        if self._link_repo is None:
            return []

        link_repo: InMemoryGraphNodeLinkDefinitionRepository = self._link_repo  # type: ignore[assignment]
        links = await link_repo.list_by_graph_definition_id(graph_definition_id)
        result: list[GraphNodeDefinition] = []
        for link in links:
            node = self._store.get(link.graph_node_definition_id.value)
            if node is not None:
                result.append(node)
        return result
