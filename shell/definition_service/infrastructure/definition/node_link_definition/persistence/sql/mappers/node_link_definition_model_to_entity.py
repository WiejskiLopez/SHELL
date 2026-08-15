from __future__ import annotations

from typing import TYPE_CHECKING

from shell.definition_service.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.definition_service.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.definition_service.domain.definition.aggregates.node_link_definition.node_link_definition import (
    NodeLinkDefinition,
)
from shell.definition_service.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
    NodeLinkDefinitionId,
)
from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt

if TYPE_CHECKING:
    from shell.definition_service.infrastructure.definition.node_link_definition.persistence.sql.models import (
        NodeLinkDefinitionModel,
    )


def node_link_definition_model_to_entity(model: NodeLinkDefinitionModel) -> NodeLinkDefinition:
    return NodeLinkDefinition.restore(
        id=NodeLinkDefinitionId(model.id),
        created_at=CreatedAt.from_datetime(model.created_at),
        changed_at=ChangedAt.from_datetime(model.changed_at),
        deleted_at=DeletedAt.from_datetime(model.deleted_at),
        graph_definition_id=GraphDefinitionId(model.graph_definition_id),
        node_definition_id=NodeDefinitionId(model.node_definition_id),
    )
