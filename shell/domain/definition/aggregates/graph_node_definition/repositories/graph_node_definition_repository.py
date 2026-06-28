from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_definition.graph_node_definition import (
        GraphNodeDefinition,
    )
    from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class GraphNodeDefinitionRepository(Protocol):
    async def get_by_id(
        self, graph_node_definition_id: GraphNodeDefinitionId,
    ) -> GraphNodeDefinition | None: ...

    async def list_by_graph_definition_id(
        self, graph_definition_id: GraphDefinitionId,
    ) -> list[GraphNodeDefinition]: ...

    async def save(self, node: GraphNodeDefinition) -> None: ...

    async def delete(self, id: GraphNodeDefinitionId) -> None: ...

    async def exists(self, id: GraphNodeDefinitionId) -> ExistsResult: ...
