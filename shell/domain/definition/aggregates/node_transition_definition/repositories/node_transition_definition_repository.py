from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.node_transition_definition.node_transition_definition import (
        NodeTransitionDefinition,
    )
    from shell.domain.definition.aggregates.node_transition_definition.value_objects.node_transition_definition_id import (
        NodeTransitionDefinitionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class NodeTransitionDefinitionRepository(Protocol):
    async def get_by_id(
        self,
        id: NodeTransitionDefinitionId,
    ) -> NodeTransitionDefinition | None: ...

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[NodeTransitionDefinition]: ...

    async def save(self, transition: NodeTransitionDefinition) -> None: ...

    async def delete(self, id: NodeTransitionDefinitionId) -> None: ...

    async def exists(self, id: NodeTransitionDefinitionId) -> ExistsResult: ...
