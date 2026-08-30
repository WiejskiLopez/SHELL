from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.graph_execution.ports.graph_definition_semantic_query import (
        GraphDefinitionSemanticQuery,
    )
    from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_definition_id_ref import (
        GraphDefinitionIdRef,
    )
    from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_definition_reference import (
        GraphDefinitionReference,
    )


class GraphDefinitionProvider(Protocol):
    async def get_graph_definition(
        self, definition_id: GraphDefinitionIdRef
    ) -> GraphDefinitionReference | None: ...

    async def get_graph_definition_by_semantic(
        self,
        query: GraphDefinitionSemanticQuery,
    ) -> GraphDefinitionReference | None: ...
