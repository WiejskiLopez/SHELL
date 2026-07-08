from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.definition.graph_definition.dto.graph_definition import (
        GraphDefinitionDto,
    )
    from shell.application.definition.graph_definition.ports.graph_definition_query_service import (
        GraphDefinitionQueryService,
    )
    from shell.application.definition.graph_definition.queries.graph_definition_get_by_id_query import (
        GraphDefinitionGetByIdQuery,
    )


class GraphDefinitionGetByIdHandler:
    def __init__(self, queries: GraphDefinitionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GraphDefinitionGetByIdQuery) -> GraphDefinitionDto | None:
        return await self._queries.get_by_id(query.definition_id)
