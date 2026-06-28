from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_transition_definition.graph_node_transition_definition import (
        GraphNodeTransitionDefinition,
    )
    from shell.domain.definition.aggregates.graph_node_transition_definition.value_objects.graph_node_transition_definition_id import (
        GraphNodeTransitionDefinitionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class GraphNodeTransitionDefinitionRepository(Protocol):
    async def get_by_id(
        self, id: GraphNodeTransitionDefinitionId,
    ) -> GraphNodeTransitionDefinition | None: ...

    async def list_by_graph_definition_id(
        self, graph_definition_id: GraphDefinitionId,
    ) -> list[GraphNodeTransitionDefinition]: ...

    async def save(self, transition: GraphNodeTransitionDefinition) -> None: ...

    async def delete(self, id: GraphNodeTransitionDefinitionId) -> None: ...

    async def exists(self, id: GraphNodeTransitionDefinitionId) -> ExistsResult: ...
