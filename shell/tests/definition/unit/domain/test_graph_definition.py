from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.events.graph_definition_created_event import (
    GraphDefinitionCreatedEvent,
)
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.value_objects.graph_name import GraphName
from shell.domain.definition.value_objects.purpose import Purpose


class TestGraphDefinition:
    def test_constructor_sets_name_and_purpose(self) -> None:
        graph_definition = GraphDefinition(GraphDefinitionId("g1"), GraphName("test"), Purpose("for testing"))
        assert graph_definition.name == GraphName("test")
        assert graph_definition.purpose == Purpose("for testing")

    def test_constructor_empty_ids(self) -> None:
        graph_definition = GraphDefinition(GraphDefinitionId("g1"), GraphName("x"), Purpose("y"))
        assert len(graph_definition.graph_node_definition_ids) == 0
        assert len(graph_definition.transition_definition_ids) == 0

    def test_create_emits_event(self) -> None:
        now = datetime.now(UTC)
        graph_definition = GraphDefinition.create(
            id=GraphDefinitionId("g1"),
            name=GraphName("test"),
            purpose=Purpose("for testing"),
            now=now,
        )
        assert graph_definition.name == GraphName("test")
        assert graph_definition.purpose == Purpose("for testing")
        events = graph_definition.pull_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, GraphDefinitionCreatedEvent)
        assert event.graph_definition_id == GraphDefinitionId("g1")
        assert event.name == GraphName("test")
        assert event.purpose == Purpose("for testing")

    def test_create_with_node_ids(self) -> None:
        from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
            GraphNodeDefinitionId,
        )

        now = datetime.now(UTC)
        node_id = GraphNodeDefinitionId("n1")
        graph_definition = GraphDefinition.create(
            id=GraphDefinitionId("g1"),
            name=GraphName("test"),
            purpose=Purpose("testing"),
            graph_node_definition_ids=[node_id],
            now=now,
        )
        assert list(graph_definition.graph_node_definition_ids) == [node_id]
