from __future__ import annotations

from shell.application.definition.dto.graph_definition import GraphDefinitionDto
from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.value_objects.graph_name import GraphName
from shell.domain.definition.value_objects.ids import (
    NodeTransitionDefinitionId,
)
from shell.domain.definition.value_objects.purpose import Purpose
from shell.domain.definition.value_objects.system_role import SystemRole
from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel,
)


def graph_definition_model_to_dto(model: GraphDefinitionModel) -> GraphDefinitionDto:
    return GraphDefinitionDto(
        id=model.id,
        name=model.name,
        purpose=model.purpose,
        system_role=model.system_role,
        node_definitions=[],
    )


def graph_definition_model_to_entity(model: GraphDefinitionModel) -> GraphDefinition:
    transition_ids = [
        NodeTransitionDefinitionId(t.id)
        for t in (model.node_transition_definition_models or [])
    ]
    system_role = SystemRole(model.system_role) if model.system_role is not None else None
    return GraphDefinition(
        id=GraphDefinitionId(model.id),
        name=GraphName(model.name),
        purpose=Purpose(model.purpose),
        system_role=system_role,
        transition_definition_ids=transition_ids,
    )


def graph_definition_entity_to_model(entity: GraphDefinition) -> GraphDefinitionModel:
    return GraphDefinitionModel(
        id=str(entity.id.value),
        name=str(entity.name.value),
        purpose=str(entity.purpose.value),
        system_role=str(entity.system_role.value) if entity.system_role is not None else None,
    )
