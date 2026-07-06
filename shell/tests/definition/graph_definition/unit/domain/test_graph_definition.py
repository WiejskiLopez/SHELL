from __future__ import annotations

from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)


class TestGraphDefinition:
    def test_create_graph_definition(self) -> None:
        gd = GraphDefinition(
            id=GraphDefinitionId("gd-2"),
        )
        assert gd.id.value == "gd-2"
