from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.entities.graph_definition import GraphDefinition
    from shell.domain.platform.value_objects.ids import GraphDefinitionId


class DefinitionProvider(Protocol):
    def get_graph_definition(self, id: GraphDefinitionId) -> GraphDefinition: ...
