from __future__ import annotations

from datetime import datetime, UTC

import pytest

from shell.domain.entities.workflow import Workflow
from shell.domain.exceptions import InvalidWorkflowTransition
from shell.domain.events.events import (
    NodeAdvanced,
    NodeStarted,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from shell.domain.value_objects.ids import (
    NodeId,
    TaskId,
    WorkflowId,
)
from shell.domain.value_objects.status import Status
from shell.domain.value_objects.workflow_cursor import WorkflowCursor
from shell.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)

# Definicja stałej czasowej zgodna z konwencją w dump_004.md
_NOW = datetime(2026, 6, 16, 12, 0, 0, tzinfo=UTC)


def _new_workflow() -> Workflow:
    """Pomocnicza fabryka agregatu Workflow oparta o sygnaturę z dump_002.md."""
    return Workflow.new(
        id_=WorkflowId("wf-123"),
        task_id=TaskId("task-456"),
        now=_NOW,
    )


def _ctx() -> WorkflowExecutionContext:
    """Pomocniczy kontekst wykonania mapowany w infrastructure/persistence/sql/mappers."""
    return WorkflowExecutionContext(
        work_dir="/tmp/shell_work",
        correlation_id="corr-abc-123",
    )


class TestWorkflowStateMachine:
    def test_workflow_initial_state_is_idle(self) -> None:
        """Weryfikuje, czy nowo utworzony workflow ma status idle i pusty cursor."""
        wf = _new_workflow()

        assert wf.status == Status.idle()
        assert wf.cursor == WorkflowCursor.empty()
        assert wf.node_states == {}

    def test_start_at_transitions_to_running_and_emits_events(self) -> None:
        """Weryfikuje przejście ze stanu idle do running po wywołaniu start_at."""
        wf = _new_workflow()
        first_node = NodeId("node-start")

        wf.start_at(first_node_id=first_node, context=_ctx(), now=_NOW)

        assert wf.status == Status.running()
        assert wf.cursor == WorkflowCursor.at(first_node)
        assert first_node.value in wf.node_states
        assert wf.node_states[first_node.value].status == Status.running()

        # Sprawdzenie akumulacji zdarzeń domenowych
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowStarted) for e in events)
        assert any(isinstance(e, NodeStarted) for e in events)

    def test_start_at_raises_invalid_transition_if_not_idle(self) -> None:
        """Próba ponownego wystartowania uruchomionego workflow rzuca wyjątek."""
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("node-1"), context=_ctx(), now=_NOW)

        with pytest.raises(InvalidWorkflowTransition):
            wf.start_at(first_node_id=NodeId("node-2"), context=_ctx(), now=_NOW)

    def test_advance_to_moves_cursor_to_next_node(self) -> None:
        """Weryfikuje poprawne przesunięcie cursora do kolejnego węzła."""
        wf = _new_workflow()
        node1 = NodeId("node-1")
        node2 = NodeId("node-2")

        wf.start_at(first_node_id=node1, context=_ctx(), now=_NOW)
        wf.pull_events()  # Czyszczenie eventów startowych

        wf.advance_to(next_node_id=node2, now=_NOW)

        assert wf.cursor == WorkflowCursor.at(node2)
        assert wf.node_states[node2.value].status == Status.running()

        events = wf.pull_events()
        assert any(isinstance(e, NodeAdvanced) for e in events)
        assert any(isinstance(e, NodeStarted) for e in events)

    def test_advance_to_raises_if_workflow_not_running(self) -> None:
        """Nie można przesunąć cursora, jeśli workflow nie wystartował."""
        wf = _new_workflow()

        with pytest.raises(InvalidWorkflowTransition):
            wf.advance_to(next_node_id=NodeId("node-2"), now=_NOW)

    def test_finish_transitions_to_done_and_clears_cursor(self) -> None:
        """Weryfikuje poprawne zakończenie workflow i przejście w stan terminalny done."""
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("node-1"), context=_ctx(), now=_NOW)
        wf.pull_events()

        wf.finish(now=_NOW)

        assert wf.status == Status.done()
        assert wf.cursor == WorkflowCursor.empty()

        events = wf.pull_events()
        assert any(isinstance(e, WorkflowCompleted) for e in events)

    def test_abort_transitions_to_failed_and_clears_cursor(self) -> None:
        """Weryfikuje zachowanie metody abort na podstawie struktury TestAbort z dump_004.md."""
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("node-1"), context=_ctx(), now=_NOW)
        wf.pull_events()

        wf.abort(reason="Wymuszone zatrzymanie awaryjne", now=_NOW)

        assert wf.status == Status.failed()
        assert wf.cursor == WorkflowCursor.empty()

        events = wf.pull_events()
        assert any(isinstance(e, WorkflowFailed) for e in events)