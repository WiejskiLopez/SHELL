from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.definition_service.framework.definition.graph_definition.api.controller import (
    GraphDefinitionController,
)
from shell.definition_service.framework.definition.graph_definition.api.graph_definition_response import (
    GraphDefinitionResponse,
)
from shell.definition_service.framework.definition.graph_definition.api.semantic_query_request import (
    SemanticQueryRequest,  # noqa: TC001 — Pydantic model wymagany przez FastAPI w runtime
)
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.dependencies import get_query_bus

router = APIRouter(prefix="/graph-definitions", tags=["GraphDefinitions"])


def get_graph_definition_controller(
    query_bus: QueryBus = Depends(get_query_bus),
) -> GraphDefinitionController:
    return GraphDefinitionController(query_bus)


@router.get("/{graph_definition_id}", response_model=GraphDefinitionResponse)
async def get_graph_definition(
    graph_definition_id: str,
    controller: GraphDefinitionController = Depends(get_graph_definition_controller),
) -> GraphDefinitionResponse:
    return await controller.get_graph_definition(graph_definition_id)


@router.post("/by-semantic", response_model=GraphDefinitionResponse)
async def get_graph_definition_by_semantic(
    body: SemanticQueryRequest,
    controller: GraphDefinitionController = Depends(get_graph_definition_controller),
) -> GraphDefinitionResponse:
    return await controller.get_graph_definition_by_semantic(body)
