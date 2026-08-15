from __future__ import annotations

from shell.platform.domain.base.entity_id import EntityId


class NodeDefinitionIdRef(EntityId):
    """Execution BC's reference to a NodeDefinition from definition BC.

    Intentionally duplicated for BC isolation.
    See shell.definition_service.domain.definition.aggregates.node_definition.value_objects.node_definition_id.NodeDefinitionId
    """

    pass
