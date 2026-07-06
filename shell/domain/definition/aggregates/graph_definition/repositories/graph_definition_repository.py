from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class GraphDefinitionRepository(Protocol):
    async def get(self, graph_execution_id: GraphDefinitionId) -> GraphDefinition | None: ...

    async def save(self, graph: GraphDefinition) -> None: ...

    async def delete(self, id: GraphDefinitionId) -> None: ...

    async def exists(self, id: GraphDefinitionId) -> ExistsResult: ...
