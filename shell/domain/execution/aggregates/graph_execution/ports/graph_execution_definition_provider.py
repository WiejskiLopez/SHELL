from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.ports.graph_definition_semantic_query import (
        GraphDefinitionSemanticQuery,  # noqa: TC002 — używany w sygnaturze Protocol
    )
    from shell.domain.execution.value_objects.graph_execution_definition import (
        GraphExecutionDefinition,  # noqa: TC002 — GraphExecutionDefinition używany w sygnaturach Protocol
    )


class GraphExecutionDefinitionProvider(Protocol):
    async def get_graph_definition(self, definition_id: str) -> GraphExecutionDefinition | None: ...

    async def get_graph_definition_by_semantic_name(
        self,
        query: GraphDefinitionSemanticQuery,
    ) -> GraphExecutionDefinition | None: ...
