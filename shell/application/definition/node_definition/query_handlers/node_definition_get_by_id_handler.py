from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.definition.node_definition.dto.node_definition import (
        NodeDefinitionDto,
    )
    from shell.application.definition.node_definition.ports.node_definition_query_service import (
        NodeDefinitionQueryService,
    )
    from shell.application.definition.node_definition.queries.node_definition_get_by_id_query import (
        NodeDefinitionGetByIdQuery,
    )


class NodeDefinitionGetByIdHandler:
    def __init__(self, queries: NodeDefinitionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: NodeDefinitionGetByIdQuery) -> NodeDefinitionDto | None:
        return await self._queries.get_by_id(query.node_definition_id)
