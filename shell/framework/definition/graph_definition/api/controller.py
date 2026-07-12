from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

if TYPE_CHECKING:
    from shell.application.definition.graph_definition.dto.graph_definition import (
        GraphDefinitionDto,
    )
    from shell.application.definition.graph_definition.ports.graph_definition_query_service import (
        GraphDefinitionQueryService,
    )
    from shell.platform.types import JsonStr


class GraphDefinitionController:
    __slots__ = ("_query_service",)

    def __init__(self, query_service: GraphDefinitionQueryService) -> None:
        self._query_service = query_service

    async def get_graph_definition(self, graph_definition_id: str) -> GraphDefinitionDto:
        result = await self._query_service.get_by_id(graph_definition_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Graph definition '{graph_definition_id}' not found")
        return result

    async def get_graph_definition_by_semantic(
        self, semantic_query: JsonStr
    ) -> GraphDefinitionDto:
        result = await self._query_service.get_graph_definition_by_semantic(semantic_query)
        if result is None:
            raise HTTPException(
                status_code=404, detail="No definition found for the given semantic query"
            )
        return result
