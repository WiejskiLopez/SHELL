from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_link_definition.graph_node_link_definition import (
        GraphNodeLinkDefinition,
    )
    from shell.domain.definition.aggregates.graph_node_link_definition.value_objects.graph_node_link_definition_id import (
        GraphNodeLinkDefinitionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class GraphNodeLinkDefinitionRepository(Protocol):
    async def get_by_id(
        self,
        graph_node_link_definition_id: GraphNodeLinkDefinitionId,
    ) -> GraphNodeLinkDefinition | None: ...

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[GraphNodeLinkDefinition]: ...

    async def list_by_graph_node_definition_id(
        self,
        graph_node_definition_id: GraphNodeDefinitionId,
    ) -> list[GraphNodeLinkDefinition]: ...

    async def save(self, link: GraphNodeLinkDefinition) -> None: ...

    async def delete(self, id: GraphNodeLinkDefinitionId) -> None: ...

    async def exists(self, id: GraphNodeLinkDefinitionId) -> ExistsResult: ...
