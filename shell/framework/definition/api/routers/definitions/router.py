from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from shell.application.definition.dto.graph_definition import GraphDefinitionDto
from shell.framework.definition.api.routers.definitions.controller import DefinitionController
from shell.framework.platform.api.dependencies import get_core_container

if TYPE_CHECKING:
    from shell.application.definition.ports.queries.graph_definition_query_service import (
        GraphDefinitionQueryService,
    )
    from shell.bootstrap.platform.container.core_container import CoreContainer

router = APIRouter(prefix="/definitions", tags=["definitions"])


def get_definition_controller(
    container: CoreContainer = Depends(get_core_container),
) -> DefinitionController:
    query_service: GraphDefinitionQueryService = container.infra.graph_definition_query_service_factory()
    return DefinitionController(query_service)


@router.get("/{definition_id}", response_model=GraphDefinitionDto)
async def get_definition(
    definition_id: str,
    controller: DefinitionController = Depends(get_definition_controller),
) -> GraphDefinitionDto:
    return await controller.get_definition(definition_id)


@router.post("/by-semantic-name", response_model=GraphDefinitionDto)
async def get_definition_by_semantic_name(
    payload: dict[str, object],
    controller: DefinitionController = Depends(get_definition_controller),
) -> GraphDefinitionDto:
    return await controller.get_definition_by_semantic_name(payload)
