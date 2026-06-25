from __future__ import annotations

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.value_objects.transition_definition import (
    TransitionDefinition,
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.services.graph_node_execution_navigator.transition_based_navigator import (
    TransitionBasedGraphNodeExecutionNavigator,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    GraphNodeTransitionExecutionId,
    TaskExecutionId,
)
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.execution.value_objects.edge_type import EdgeType


def _make_node(node_id: str, position: int, mode: str = "agent") -> GraphNodeExecution:
    return GraphNodeExecution(
        id=GraphNodeExecutionId(node_id),
        position=position,
        mode=Mode(mode),
        role=mode,
        node_type=mode,
    )


def _make_transition(
    transition_id: str,
    from_node_id: str | None,
    to_node_id: str,
    ttype: EdgeType = EdgeType.SEQUENCE,
    priority: int = 0,
    condition: str | None = None,
) -> TransitionDefinition:
    return TransitionDefinition(
        source_node_execution_id=from_node_id or "",
        target_node_execution_id=to_node_id,
        edge_type=ttype,
        priority=priority,
        label=f"{from_node_id}_to_{to_node_id}",
        condition_expression=condition,
    )


def _make_graph(
    *nodes: GraphNodeExecution, transitions: list[TransitionDefinition] | None = None
) -> GraphExecution:
    return GraphExecution(
        id=GraphExecutionId("ge"),
        task_execution_id=TaskExecutionId("t1"),
        depth=1,
        transitions=transitions,
    )


class TestTransitionBasedGraphNodeExecutionNavigatorFirst:
    def setup_method(self) -> None:
        self._nav = TransitionBasedGraphNodeExecutionNavigator()

    def test_first_no_transitions_falls_back_to_position(self) -> None:
        a = _make_node("a", 1)
        b = _make_node("b", 2)
        ge = _make_graph(a, b)
        result = self._nav.first(ge)
        assert result is not None
        assert result.id == GraphNodeExecutionId("a")

    def test_first_uses_start_transition(self) -> None:
        a = _make_node("a", 2)
        b = _make_node("b", 1)
        ge = _make_graph(
            a,
            b,
            transitions=[
                _make_transition("t1", None, "b"),
            ],
        )
        result = self._nav.first(ge)
        assert result is not None
        assert result.id == GraphNodeExecutionId("b")

    def test_first_picks_lowest_priority_start(self) -> None:
        a = _make_node("a", 1)
        b = _make_node("b", 2)
        ge = _make_graph(
            a,
            b,
            transitions=[
                _make_transition("t1", None, "b", priority=10),
                _make_transition("t2", None, "a", priority=0),
            ],
        )
        result = self._nav.first(ge)
        assert result is not None
        assert result.id == GraphNodeExecutionId("a")

    def test_first_empty_graph_returns_none(self) -> None:
        ge = _make_graph()
        assert self._nav.first(ge) is None


class TestTransitionBasedGraphNodeExecutionNavigatorNextAfter:
    def setup_method(self) -> None:
        self._nav = TransitionBasedGraphNodeExecutionNavigator()
        self._a = _make_node("a", 1)
        self._b = _make_node("b", 2)
        self._c = _make_node("c", 3)

    def test_sequence_transition_returns_target(self) -> None:
        ge = _make_graph(
            self._a,
            self._b,
            transitions=[
                _make_transition("t1", "a", "b", EdgeType.SEQUENCE),
            ],
        )
        result = list(self._nav.next_after(ge, GraphNodeExecutionId("a")))
        assert len(result) == 1
        assert result[0].id == GraphNodeExecutionId("b")

    def test_conditional_transitions_are_skipped_in_next_after(self) -> None:
        ge = _make_graph(
            self._a,
            self._b,
            transitions=[
                _make_transition("t1", "a", "b", EdgeType.CONDITIONAL, condition="true"),
            ],
        )
        result = list(self._nav.next_after(ge, GraphNodeExecutionId("a")))
        assert len(result) == 0

    def test_error_handler_transitions_are_skipped_in_next_after(self) -> None:
        ge = _make_graph(
            self._a,
            self._b,
            transitions=[
                _make_transition("t1", "a", "b", EdgeType.ERROR_HANDLER),
            ],
        )
        result = list(self._nav.next_after(ge, GraphNodeExecutionId("a")))
        assert len(result) == 0

    def test_default_fallback_when_no_direct_match(self) -> None:
        ge = _make_graph(
            self._a,
            self._b,
            transitions=[
                _make_transition("t1", "a", "b", EdgeType.DEFAULT),
            ],
        )
        result = list(self._nav.next_after(ge, GraphNodeExecutionId("a")))
        assert len(result) == 1
        assert result[0].id == GraphNodeExecutionId("b")

    def test_no_transitions_returns_empty(self) -> None:
        ge = _make_graph(self._a, self._b)
        result = list(self._nav.next_after(ge, GraphNodeExecutionId("a")))
        assert len(result) == 0


class TestTransitionBasedGraphNodeExecutionNavigatorNextConditional:
    def test_returns_conditional_targets_with_expressions(self) -> None:
        nav = TransitionBasedGraphNodeExecutionNavigator()
        a = _make_node("a", 1)
        b = _make_node("b", 2)
        c = _make_node("c", 3)
        ge = _make_graph(
            a,
            b,
            c,
            transitions=[
                _make_transition("t1", "a", "b", EdgeType.CONDITIONAL, condition="true"),
                _make_transition("t2", "a", "c", EdgeType.CONDITIONAL, condition="false"),
                _make_transition("t3", "a", "c", EdgeType.SEQUENCE),
            ],
        )
        result = nav.next_conditional(ge, GraphNodeExecutionId("a"))
        assert len(result) == 2

    def no_condition_expression_is_skipped(self) -> None:
        nav = TransitionBasedGraphNodeExecutionNavigator()
        a = _make_node("a", 1)
        b = _make_node("b", 2)
        ge = _make_graph(
            a,
            b,
            transitions=[
                _make_transition("t1", "a", "b", EdgeType.CONDITIONAL, condition=None),
            ],
        )
        result = nav.next_conditional(ge, GraphNodeExecutionId("a"))
        assert len(result) == 0


class TestTransitionBasedGraphNodeExecutionNavigatorNextErrorHandler:
    def test_returns_error_handler_target(self) -> None:
        nav = TransitionBasedGraphNodeExecutionNavigator()
        a = _make_node("a", 1)
        b = _make_node("b", 2)
        ge = _make_graph(
            a,
            b,
            transitions=[
                _make_transition("t1", "a", "b", EdgeType.ERROR_HANDLER),
            ],
        )
        result = nav.next_error_handler(ge, GraphNodeExecutionId("a"))
        assert result is not None
        assert result.id == GraphNodeExecutionId("b")

    def test_no_error_handler_returns_none(self) -> None:
        nav = TransitionBasedGraphNodeExecutionNavigator()
        a = _make_node("a", 1)
        ge = _make_graph(a)
        result = nav.next_error_handler(ge, GraphNodeExecutionId("a"))
        assert result is None


class TestTransitionBasedGraphNodeExecutionNavigatorNextLoopTarget:
    def test_returns_loop_target(self) -> None:
        nav = TransitionBasedGraphNodeExecutionNavigator()
        a = _make_node("a", 1)
        b = _make_node("b", 2)
        ge = _make_graph(
            a,
            b,
            transitions=[
                _make_transition("t1", "a", "b", EdgeType.LOOP),
            ],
        )
        result = nav.next_loop_target(ge, GraphNodeExecutionId("a"))
        assert result is not None
        assert result.id == GraphNodeExecutionId("b")

    def test_no_loop_returns_none(self) -> None:
        nav = TransitionBasedGraphNodeExecutionNavigator()
        a = _make_node("a", 1)
        ge = _make_graph(a)
        result = nav.next_loop_target(ge, GraphNodeExecutionId("a"))
        assert result is None
