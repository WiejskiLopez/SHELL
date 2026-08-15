from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.base.value_object import ValueObject

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_definition_id_ref import (
        GraphDefinitionIdRef,
    )


@dataclass(frozen=True, slots=True)
class GraphDefinitionReference(ValueObject):
    """Reference to a graph definition owned by the definition BC."""

    graph_definition_id: GraphDefinitionIdRef
