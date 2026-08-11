from __future__ import annotations

from typing import TYPE_CHECKING

from shell.definition.domain.definition.aggregates.node_definition.node_definition import (
    NodeDefinition,
)
from shell.definition.domain.definition.aggregates.node_definition.repositories import (
    NodeDefinitionRepository,
)
from shell.definition.domain.definition.aggregates.node_definition.value_objects import (
    NodeDefinitionId,
)
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.definition.domain.definition.aggregates.graph_definition.value_objects import (
        GraphDefinitionId,
    )
    from shell.definition.infrastructure.definition.node_link_definition.persistence.memory.in_memory_node_link_definition_repository import (
        InMemoryNodeLinkDefinitionRepository,
    )


class InMemoryNodeDefinitionRepository(
    InMemoryRepository[NodeDefinition, NodeDefinitionId], NodeDefinitionRepository
):
    def __init__(self) -> None:
        super().__init__()
        self._link_repo: object = None

    def set_link_repository(self, link_repo: object) -> None:
        self._link_repo = link_repo

    async def save(self, node: NodeDefinition) -> None:
        self._store[node.id.value] = node

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[NodeDefinition]:
        if self._link_repo is None:
            return []

        link_repo: InMemoryNodeLinkDefinitionRepository = self._link_repo  # type: ignore[assignment]
        links = await link_repo.list_by_graph_definition_id(graph_definition_id)
        result: list[NodeDefinition] = []
        for link in links:
            node = self._store.get(link.node_definition_id.value)
            if node is not None:
                result.append(node)
        return result
