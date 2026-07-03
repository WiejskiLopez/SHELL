from __future__ import annotations

from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.value_objects.graph_name import GraphName
from shell.domain.definition.value_objects.purpose import Purpose


class TestGraphDefinition:
    def test_constructor_empty_ids(self) -> None:
        gd = GraphDefinition(
            id=GraphDefinitionId("gd-1"),
            name=GraphName("test"),
            purpose=Purpose("testing"),
        )
        assert gd.transition_definition_ids == ()

    def test_create_with_transition_ids(self) -> None:
        gd = GraphDefinition(
            id=GraphDefinitionId("gd-2"),
            name=GraphName("test2"),
            purpose=Purpose("testing"),
        )
        assert gd.name.value == "test2"
        assert gd.purpose.value == "testing"
