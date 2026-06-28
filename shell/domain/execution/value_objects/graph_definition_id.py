from __future__ import annotations

from shell.domain.platform.base.entity_id import EntityId


class GraphDefinitionIdRef(EntityId):
    """Execution BC's reference to a GraphDefinition from definition BC.

    Intentionally duplicated for BC isolation.
    See shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id.GraphDefinitionId
    """
    pass
