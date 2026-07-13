from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from shell.framework.definition.graph_definition.api.controller import GraphDefinitionController
from shell.framework.definition.graph_definition.api.graph_definition_response import (
    GraphDefinitionResponse,
)
from shell.framework.definition.graph_definition.api.semantic_query_request import (
    SemanticQueryRequest,  # noqa: TC001 — Pydantic model wymagany przez FastAPI w runtime
)
from shell.platform.framework.api.dependencies import get_core_container
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from shell.application.definition.graph_definition.ports.graph_definition_query_service import (
        GraphDefinitionQueryService,
    )
    from shell.platform.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/graph-definitions", tags=["graph-definitions"])


def get_graph_definition_controller(
    container: CoreContainer = Depends(get_core_container),
) -> GraphDefinitionController:
    query_service: GraphDefinitionQueryService = (
        container.infra.graph_definition_query_service_factory()
    )
    return GraphDefinitionController(query_service)


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
    return await controller.get_graph_definition_by_semantic(JsonStr(json.dumps(body.model_dump())))
