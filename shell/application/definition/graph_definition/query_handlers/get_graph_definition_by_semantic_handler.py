from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.platform.domain.types import JsonStr

if TYPE_CHECKING:
    from shell.application.definition.graph_definition.dto.graph_definition import (
        GraphDefinitionDto,
    )
    from shell.application.definition.graph_definition.ports.graph_definition_query_service import (
        GraphDefinitionQueryService,
    )
    from shell.application.definition.graph_definition.queries.get_graph_definition_by_semantic_query import (
        GetGraphDefinitionBySemanticQuery,
    )


class GetGraphDefinitionBySemanticHandler:
    def __init__(self, queries: GraphDefinitionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetGraphDefinitionBySemanticQuery) -> GraphDefinitionDto | None:
        semantic_query: dict[str, object] = {
            "query": query.query,
            "purpose": query.purpose,
            "limit": query.limit,
        }
        if query.default_graph_definition_id is not None:
            semantic_query["default_graph_definition_id"] = query.default_graph_definition_id
        return await self._queries.get_graph_definition_by_semantic(JsonStr(json.dumps(semantic_query)))