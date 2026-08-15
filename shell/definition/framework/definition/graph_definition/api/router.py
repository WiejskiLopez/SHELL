from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from shell.definition.framework.definition.graph_definition.api.controller import (
    GraphDefinitionController,
)
from shell.definition.framework.definition.graph_definition.api.graph_definition_response import (
    GraphDefinitionResponse,
)
from shell.definition.framework.definition.graph_definition.api.semantic_query_request import (
    SemanticQueryRequest,  # noqa: TC001 — Pydantic model wymagany przez FastAPI w runtime
)
from shell.platform.framework.api.dependencies import get_core_container
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol

router = APIRouter(prefix="/graph-definitions", tags=["GraphDefinitions"])


def get_graph_definition_controller(
    container: ContainerProtocol = Depends(get_core_container),
) -> GraphDefinitionController:
    query_service = (
        container.infra.graph_definition_query_service_factory()
        if hasattr(container, "app")
        else getattr(container, "graph_definition_query_service")()  # noqa: B009 -- atrybut spoza ContainerProtocol, direct access daje mypy attr-defined
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
