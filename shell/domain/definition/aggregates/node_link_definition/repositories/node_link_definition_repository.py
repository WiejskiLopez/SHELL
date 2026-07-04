from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
        NodeDefinitionId,
    )
    from shell.domain.definition.aggregates.node_link_definition.node_link_definition import (
        NodeLinkDefinition,
    )
    from shell.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
        NodeLinkDefinitionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class NodeLinkDefinitionRepository(Protocol):
    async def get_by_id(
        self,
        node_link_definition_id: NodeLinkDefinitionId,
    ) -> NodeLinkDefinition | None: ...

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[NodeLinkDefinition]: ...

    async def list_by_node_definition_id(
        self,
        node_definition_id: NodeDefinitionId,
    ) -> list[NodeLinkDefinition]: ...

    async def save(self, link: NodeLinkDefinition) -> None: ...

    async def delete(self, id: NodeLinkDefinitionId) -> None: ...

    async def exists(self, id: NodeLinkDefinitionId) -> ExistsResult: ...
