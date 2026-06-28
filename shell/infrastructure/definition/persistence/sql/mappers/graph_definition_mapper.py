from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.dto.graph_definition import GraphDefinitionDto
from shell.application.definition.dto.graph_node_definition import GraphNodeDefinitionDto

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
    from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_transition_definition.value_objects.graph_node_transition_definition_id import (
        GraphNodeTransitionDefinitionId,
    )
    from shell.infrastructure.definition.persistence.sql.models import (
        GraphDefinitionModel,
    )


def graph_definition_model_to_dto(model: GraphDefinitionModel) -> GraphDefinitionDto:
    return GraphDefinitionDto(
        id=model.id,
        name=model.name,
        purpose=model.purpose,
        system_role=model.system_role,
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
    from shell.domain.definition.value_objects.system_role import SystemRole
    from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )

    node_ids = [
        GraphNodeDefinitionId(nd.id)
        for nd in (model.graph_node_execution_models or [])
    ]
    transition_ids = [
        GraphNodeTransitionDefinitionId(t.id)
        for t in (model.graph_node_transition_definition_models or [])
    ]
    system_role = SystemRole(model.system_role) if model.system_role is not None else None
    return GraphDefinition(
        id=GraphDefinitionId(model.id),
        name=model.name,
        purpose=model.purpose,
        system_role=system_role,
        graph_node_definition_ids=node_ids,
        transition_definition_ids=transition_ids,
    )


def graph_definition_entity_to_model(entity: GraphDefinition) -> GraphDefinitionModel:
    return GraphDefinitionModel(
        id=str(entity.id.value),
        name=str(entity.name.value),
        purpose=str(entity.purpose.value),
        system_role=str(entity.system_role.value) if entity.system_role is not None else None,
    )
