from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.node_definition.node_definition import (
        NodeDefinition,
    )
    from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
        NodeDefinitionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class NodeDefinitionRepository(Protocol):
    async def get_by_id(
        self,
        node_definition_id: NodeDefinitionId,
    ) -> NodeDefinition | None: ...

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[NodeDefinition]: ...

    async def save(self, node: NodeDefinition) -> None: ...

    async def delete(self, id: NodeDefinitionId) -> None: ...

    async def exists(self, id: NodeDefinitionId) -> ExistsResult: ...
