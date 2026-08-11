from __future__ import annotations

from typing import TYPE_CHECKING

from shell.definition.domain.definition.aggregates.node_link_definition.node_link_definition import (
    NodeLinkDefinition,
)
from shell.definition.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
    NodeLinkDefinitionId,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from datetime import datetime

    from shell.definition.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.definition.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
        NodeDefinitionId,
    )


class InMemoryNodeLinkDefinitionRepository(
    InMemoryRepository[NodeLinkDefinition, NodeLinkDefinitionId],
):
    async def get_by_id(
        self,
        node_link_definition_id: NodeLinkDefinitionId,
    ) -> NodeLinkDefinition | None:
        return self._store.get(node_link_definition_id.value)

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[NodeLinkDefinition]:
        return [
            link for link in self._store.values() if link.graph_definition_id == graph_definition_id
        ]

    async def list_by_node_definition_id(
        self,
        node_definition_id: NodeDefinitionId,
    ) -> list[NodeLinkDefinition]:
        return [
            link for link in self._store.values() if link.node_definition_id == node_definition_id
        ]

    async def save(self, link: NodeLinkDefinition) -> None:
        self._store[link.id.value] = link

    async def delete(self, id: NodeLinkDefinitionId, now: datetime | None = None) -> None:
        self._store.pop(id.value, None)

    async def exists(self, id: NodeLinkDefinitionId) -> ExistsResult:
        return ExistsResult(id.value in self._store)
