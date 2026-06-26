from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.dto.graph_definition import GraphDefinitionDto
from shell.application.definition.dto.graph_node_definition import GraphNodeDefinitionDto

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.entities.graph_node_definition import (
        GraphNodeDefinition,
    )
    from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )
    from shell.infrastructure.definition.persistence.sql.models import (
        GraphDefinitionModel,
        GraphNodeDefinitionModel,
    )


def graph_definition_model_to_dto(model: GraphDefinitionModel) -> GraphDefinitionDto:
    return GraphDefinitionDto(
        id=model.id,
        name=model.name,
        purpose=model.purpose,
        graph_node_definitions=[
            GraphNodeDefinitionDto(
                id=graph_node_definition.id,
                position=graph_node_definition.position,
                mode=graph_node_definition.mode,
                role=graph_node_definition.role,
                node_type=graph_node_definition.node_type,
                model=graph_node_definition.model or "",
                command=graph_node_definition.command,
                timeout=graph_node_definition.timeout,
                retries=graph_node_definition.retries,
                log_level=graph_node_definition.log_level,
                max_step=graph_node_definition.max_step,
                no_ask_user=graph_node_definition.no_ask_user or False,
                autopilot=graph_node_definition.autopilot or False,
                status_initial=graph_node_definition.status_initial,
                script=graph_node_definition.script or "",
                script_type=graph_node_definition.script_type or "",
            )
            for graph_node_definition in model.graph_node_execution_models or []
        ],
    )


def graph_definition_model_to_entity(model: GraphDefinitionModel) -> GraphDefinition:
    from shell.domain.definition.aggregates.graph_definition.entities.graph_node_definition import (
        GraphNodeDefinition,
    )
    from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )

    nodes = [
        GraphNodeDefinition(
            id=GraphNodeDefinitionId(nd.id),
            position=nd.position,
            mode=nd.mode,
            role=nd.role,
            node_type=nd.node_type,
            model=nd.model or "",
            command=nd.command,
            timeout=nd.timeout,
            retries=nd.retries,
            log_level=nd.log_level,
            max_step=nd.max_step,
            no_ask_user=nd.no_ask_user or False,
            autopilot=nd.autopilot or False,
            status_initial=nd.status_initial,
            script=nd.script or "",
            script_type=nd.script_type or "",
        )
        for nd in model.graph_node_execution_models or []
    ]
    return GraphDefinition(
        id=GraphDefinitionId(model.id),
        name=model.name,
        purpose=model.purpose,
        graph_node_definitions=nodes,
    )


def graph_definition_entity_to_model(entity: GraphDefinition) -> GraphDefinitionModel:
    return GraphDefinitionModel(
        id=entity.id.value,
        name=entity.name,
        purpose=entity.purpose,
    )
