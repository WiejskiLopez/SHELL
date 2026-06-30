from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request as _Request

from shell.application.definition.dto.graph_definition import GraphDefinitionDto

if TYPE_CHECKING:
    from shell.application.definition.ports.queries.graph_definition_query_service import (
        GraphDefinitionQueryService,
    )
    from shell.bootstrap.platform.container.core_container import CoreContainer

router = APIRouter(prefix="/definitions", tags=["definitions"])


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


def get_graph_definition_query_service(
    container: CoreContainer = Depends(get_core_container),
) -> GraphDefinitionQueryService:
    return container.infra.graph_definition_query_service_factory()


@router.get("/{definition_id}", response_model=GraphDefinitionDto)
async def get_definition(
    definition_id: str,
    query_service: GraphDefinitionQueryService = Depends(get_graph_definition_query_service),
) -> GraphDefinitionDto | None:
    result = await query_service.get_graph_definition(definition_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Definition '{definition_id}' not found")
    return result


@router.post("/by-semantic-name", response_model=GraphDefinitionDto)
async def get_definition_by_semantic_name(
    payload: dict[str, object],
    query_service: GraphDefinitionQueryService = Depends(get_graph_definition_query_service),
) -> GraphDefinitionDto | None:
    result = await query_service.get_graph_definition_by_semantic_name(payload)
    if result is None:
        raise HTTPException(
            status_code=404, detail="No definition found for the given semantic query"
        )
    return result
