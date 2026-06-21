from __future__ import annotations

from shell.domain.definition.entities.graph_definition import GraphDefinition
from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
from shell.domain.definition.entities.graph_node_transition_definition import (
    GraphNodeTransitionDefinition,
)
from shell.domain.definition.value_objects.ids import (
    GraphDefinitionId,
    GraphNodeDefinitionId,
    GraphNodeTransitionDefinitionId,
)
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.platform.value_objects.transition_type import TransitionType


def _make_node(pos: int, mode: str) -> GraphNodeDefinition:
    return GraphNodeDefinition(
        id=GraphNodeDefinitionId.generate(),
        position=pos,
        mode=Mode(mode),
        role=mode,
        node_type=mode,
    )


def _make_transition(from_pos: int | None, to_pos: int) -> GraphNodeTransitionDefinition:
    return GraphNodeTransitionDefinition(
        id=GraphNodeTransitionDefinitionId.generate(),
        graph_definition_id=GraphDefinitionId("g1"),
        source_node_definition_id=(
            GraphNodeDefinitionId(f"n{from_pos}") if from_pos is not None else None
        ),
        target_node_definition_id=GraphNodeDefinitionId(f"n{to_pos}"),
        transition_type=TransitionType.SEQUENCE,
    )


class TestGraphDefinition:
    def test_constructor_sets_name_and_purpose(self) -> None:
        gd = GraphDefinition(GraphDefinitionId("g1"), "test", "for testing")
        assert gd.name == "test"
        assert gd.purpose == "for testing"

    def test_constructor_empty_nodes(self) -> None:
        gd = GraphDefinition(GraphDefinitionId("g1"), "x", "y")
        assert len(gd.graph_node_definitions) == 0
        assert len(gd.transition_definitions) == 0

    def test_add_node_sorts_by_position(self) -> None:
        gd = GraphDefinition(GraphDefinitionId("g1"), "x", "y")
        gd.add_graph_node_definition(_make_node(3, "agent"))
        gd.add_graph_node_definition(_make_node(1, "tool"))
        gd.add_graph_node_definition(_make_node(2, "router"))
        assert [n.position for n in gd.graph_node_definitions] == [1, 2, 3]

    def test_get_graph_node_definition_by_position(self) -> None:
        gd = GraphDefinition(GraphDefinitionId("g1"), "x", "y")
        n1 = _make_node(1, "agent")
        n2 = _make_node(2, "tool")
        gd.add_graph_node_definition(n1)
        gd.add_graph_node_definition(n2)
        node_at_1 = gd.get_graph_node_definition(1)
        assert node_at_1 is not None
        assert node_at_1.position == 1
        assert gd.get_graph_node_definition(3) is None

    def test_remove_node_by_id(self) -> None:
        gd = GraphDefinition(GraphDefinitionId("g1"), "x", "y")
        n1 = _make_node(1, "agent")
        n2 = _make_node(2, "tool")
        gd.add_graph_node_definition(n1)
        gd.add_graph_node_definition(n2)
        gd.remove_graph_node_definition(n1.id)
        assert len(gd.graph_node_definitions) == 1
        assert gd.graph_node_definitions[0].position == 2

    def test_add_transition_definition(self) -> None:
        gd = GraphDefinition(GraphDefinitionId("g1"), "x", "y")
        t = _make_transition(1, 2)
        gd.add_transition_definition(t)
        assert len(gd.transition_definitions) == 1

    def test_constructor_with_nodes_and_transitions(self) -> None:
        n1 = _make_node(1, "agent")
        t = _make_transition(1, 2)
        gd = GraphDefinition(
            GraphDefinitionId("g1"),
            "x",
            "y",
            graph_node_definitions=[n1],
            transition_definitions=[t],
        )
        assert len(gd.graph_node_definitions) == 1
        assert len(gd.transition_definitions) == 1
