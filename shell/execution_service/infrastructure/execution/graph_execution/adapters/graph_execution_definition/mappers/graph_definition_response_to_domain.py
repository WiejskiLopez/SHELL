from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_definition_id_ref import (
    GraphDefinitionIdRef,
)
from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_definition_reference import (
    GraphDefinitionReference,
)

if TYPE_CHECKING:
    from shell.execution_service.infrastructure.execution.graph_execution.adapters.graph_execution_definition.contracts.v1.graph_definition_response import (
        GraphDefinitionResponseV1,
    )


def graph_definition_response_to_domain(
    response: GraphDefinitionResponseV1,
) -> GraphDefinitionReference:
    return GraphDefinitionReference(graph_definition_id=GraphDefinitionIdRef(response.id))
