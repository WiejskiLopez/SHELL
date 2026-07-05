from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

if TYPE_CHECKING:
    from shell.application.definition.dto.graph_definition import GraphDefinitionDto
    from shell.application.definition.ports.queries.graph_definition_query_service import (
        GraphDefinitionQueryService,
    )


class DefinitionController:
    __slots__ = ("_query_service",)

    def __init__(self, query_service: GraphDefinitionQueryService) -> None:
        self._query_service = query_service

    async def get_definition(self, definition_id: str) -> GraphDefinitionDto:
        result = await self._query_service.get_graph_definition(definition_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Definition '{definition_id}' not found")
        return result

    async def get_definition_by_semantic_name(self, payload: dict[str, object]) -> GraphDefinitionDto:
        result = await self._query_service.get_graph_definition_by_semantic_name(payload)
        if result is None:
            raise HTTPException(
                status_code=404, detail="No definition found for the given semantic query"
            )
        return result
