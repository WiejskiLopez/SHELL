from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.definition_service.application.definition.graph_definition.queries.get_graph_definition_by_id_query import (
    GetGraphDefinitionByIdQuery,
)
from shell.definition_service.application.definition.graph_definition.queries.get_graph_definition_by_semantic_query import (
    GetGraphDefinitionBySemanticQuery,
)
from shell.definition_service.framework.definition.graph_definition.api.graph_definition_response import (
    GraphDefinitionResponse,
)
from shell.definition_service.framework.definition.graph_definition.api.semantic_query_request import (
    SemanticQueryRequest,
)
from shell.platform.application.bus.query_bus import QueryBus

if TYPE_CHECKING:
    from shell.definition_service.application.definition.graph_definition.dto.graph_definition import (
        GraphDefinitionDto,
    )


def _to_response(dto: GraphDefinitionDto) -> GraphDefinitionResponse:
    return GraphDefinitionResponse(
        id=dto.id,
        created_at=dto.created_at,
    )


class GraphDefinitionController:
    __slots__ = ("_query_bus",)

    def __init__(self, query_bus: QueryBus) -> None:
        self._query_bus = query_bus

    async def get_graph_definition(self, graph_definition_id: str) -> GraphDefinitionResponse:
        result = await self._query_bus.dispatch(
            GetGraphDefinitionByIdQuery(definition_id=graph_definition_id)
        )
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"Graph definition '{graph_definition_id}' not found"
            )
        return _to_response(result)

    async def get_graph_definition_by_semantic(
        self, body: SemanticQueryRequest
    ) -> GraphDefinitionResponse:
        result = await self._query_bus.dispatch(
            GetGraphDefinitionBySemanticQuery(
                query=body.query,
                purpose=body.purpose,
                limit=body.limit,
                default_graph_definition_id=body.default_graph_definition_id,
            )
        )
        if result is None:
            raise HTTPException(
                status_code=404, detail="No definition found for the given semantic query"
            )
        return _to_response(result)
