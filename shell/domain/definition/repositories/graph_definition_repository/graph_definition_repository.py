from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.entities.graph_definition import GraphDefinition
    from shell.domain.platform.value_objects.ids import GraphDefinitionId


class GraphDefinitionRepository(Protocol):
    async def get(self, graph_execution_id: GraphDefinitionId) -> GraphDefinition | None: ...

    async def get_graph_definition_by_name(
        self, graph_definition_by_name: str
    ) -> GraphDefinition | None: ...

    async def save(self, graph: GraphDefinition) -> None: ...
