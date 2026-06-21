from __future__ import annotations

from datetime import UTC, datetime

import pytest
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.events import (
    GraphNodeExecutionAdvancedEvent,
    GraphNodeExecutionStartedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    WorkflowStartedEvent,
)
from shell.domain.execution.exceptions import InvalidWorkflowTransition
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.workflow_cursor import WorkflowCursor
from shell.domain.execution.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)
from shell.domain.platform.value_objects.status import Status

# Definicja stałej czasowej zgodna z konwencją w dump_004.md
_NOW = datetime(2026, 6, 16, 12, 0, 0, tzinfo=UTC)


def _new_workflow() -> Workflow:
    """Pomocnicza fabryka agregatu Workflow oparta o sygnaturę z dump_002.md."""
    return Workflow.new(
        id_=WorkflowId("wf-123"),
        now=_NOW,
    )


def _ctx() -> WorkflowExecutionContext:
    """Pomocniczy kontekst wykonania mapowany w infrastructure/persistence/sql/mappers."""
    return WorkflowExecutionContext(
        correlation_id="corr-abc-123",
    )


class TestWorkflowStateMachine:
    def test_workflow_initial_state_is_idle(self) -> None:
        """Weryfikuje, czy nowo utworzony workflow ma status idle i pusty cursor."""
        wf = _new_workflow()

        assert wf.status == Status.idle()
        assert wf.cursor == WorkflowCursor.empty()
        assert wf.graph_node_execution_states == ()

    def test_start_at_transitions_to_running_and_emits_events(self) -> None:
        """Weryfikuje przejście ze stanu idle do running po wywołaniu start_at."""
        wf = _new_workflow()
        first_graph_node_execution_id = GraphNodeExecutionId("node-start")

        wf.start_at(
            first_graph_node_execution_id=first_graph_node_execution_id, context=_ctx(), now=_NOW,
            task_execution_id=TaskExecutionId("task-456"),
        )

        assert wf.status == Status.running()
        assert wf.cursor == WorkflowCursor.at(first_graph_node_execution_id)
        state = wf.get_graph_node_execution_state(first_graph_node_execution_id)
        assert state is not None
        assert state.status == Status.running()

        # Sprawdzenie akumulacji zdarzeń domenowych
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowStartedEvent) for e in events)
        assert any(isinstance(e, GraphNodeExecutionStartedEvent) for e in events)

    def test_start_at_raises_invalid_transition_if_not_idle(self) -> None:
        """Próba ponownego wystartowania uruchomionego workflow rzuca wyjątek."""
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("node-1"), context=_ctx(), now=_NOW
        )

        with pytest.raises(InvalidWorkflowTransition):
            wf.start_at(
                first_graph_node_execution_id=GraphNodeExecutionId("node-2"),
                context=_ctx(),
                now=_NOW,
            )

    def test_advance_to_moves_cursor_to_next_node(self) -> None:
        """Weryfikuje poprawne przesunięcie cursora do kolejnego węzła."""
        wf = _new_workflow()
        node1 = GraphNodeExecutionId("node-1")
        node2 = GraphNodeExecutionId("node-2")

        wf.start_at(first_graph_node_execution_id=node1, context=_ctx(), now=_NOW)
        wf.pull_events()  # Czyszczenie eventów startowych

        wf.advance_to(next_graph_node_execution_id=node2, now=_NOW)

        assert wf.cursor == WorkflowCursor.at(node2)
        state = wf.get_graph_node_execution_state(node2)
        assert state is not None
        assert state.status == Status.running()

        events = wf.pull_events()
        assert any(isinstance(e, GraphNodeExecutionAdvancedEvent) for e in events)
        assert any(isinstance(e, GraphNodeExecutionStartedEvent) for e in events)

    def test_advance_to_raises_if_workflow_not_running(self) -> None:
        """Nie można przesunąć cursora, jeśli workflow nie wystartował."""
        wf = _new_workflow()

        with pytest.raises(InvalidWorkflowTransition):
            wf.advance_to(next_graph_node_execution_id=GraphNodeExecutionId("node-2"), now=_NOW)

    def test_finish_transitions_to_done_and_clears_cursor(self) -> None:
        """Weryfikuje poprawne zakończenie workflow i przejście w stan terminalny done."""
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("node-1"), context=_ctx(), now=_NOW
        )
        wf.pull_events()

        wf.finish(now=_NOW, task_execution_id=TaskExecutionId("task-456"))

        assert wf.status == Status.done()
        assert wf.cursor == WorkflowCursor.empty()

        events = wf.pull_events()
        assert any(isinstance(e, WorkflowCompletedEvent) for e in events)

    def test_abort_transitions_to_failed_and_clears_cursor(self) -> None:
        """Weryfikuje zachowanie metody abort na podstawie struktury TestAbort z dump_004.md."""
        wf = _new_workflow()
        wf.start_at(
            first_graph_node_execution_id=GraphNodeExecutionId("node-1"), context=_ctx(), now=_NOW
        )
        wf.pull_events()

        wf.abort(reason="Wymuszone zatrzymanie awaryjne", now=_NOW, task_execution_id=TaskExecutionId("task-456"))

        assert wf.status == Status.failed()
        assert wf.cursor == WorkflowCursor.empty()

        events = wf.pull_events()
        assert any(isinstance(e, WorkflowFailedEvent) for e in events)
