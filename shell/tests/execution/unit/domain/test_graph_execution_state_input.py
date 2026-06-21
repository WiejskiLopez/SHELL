from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.graph_execution_state_input.graph_execution_state_input import (
    GraphExecutionStateInput,
)
from shell.domain.execution.aggregates.graph_execution_state_input.events.graph_execution_state_input_changed_event import (
    GraphExecutionStateInputChangedEvent,
)
from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphExecutionStateInputId

_NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
_GE_ID = GraphExecutionId("ge-1")


def _make_state(state_data: dict[str, object] | None = None) -> GraphExecutionStateInput:
    return GraphExecutionStateInput.create(
        id_=GraphExecutionStateInputId.generate(),
        graph_execution_id=_GE_ID,
        now=_NOW,
    )


class TestGraphExecutionStateInputCreate:
    def test_create_has_empty_state(self) -> None:
        state = _make_state()
        assert state.state_data == {}
        assert state.is_current is True
        assert state.graph_execution_id == _GE_ID

    def test_create_with_initial_data(self) -> None:
        state = GraphExecutionStateInput(
            id=GraphExecutionStateInputId.generate(),
            graph_execution_id=_GE_ID,
            state_data={"k": "v"},
            is_current=True,
            created_at=_NOW,
        )
        assert state.get("k") == "v"


class TestGraphExecutionStateInputUpdate:
    def test_update_sets_value(self) -> None:
        state = _make_state()
        state.update("key1", "value1")
        assert state.get("key1") == "value1"

    def test_update_overwrites_existing(self) -> None:
        state = _make_state()
        state.update("k", "old")
        state.update("k", "new")
        assert state.get("k") == "new"

    def test_update_emits_event(self) -> None:
        state = _make_state()
        state.update("k", "v")
        events = state.pull_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, GraphExecutionStateInputChangedEvent)
        assert event.key == "k"
        assert event.old_value is None
        assert event.new_value == "v"


class TestGraphExecutionStateInputDelete:
    def test_delete_removes_key(self) -> None:
        state = _make_state()
        state.update("k", "v")
        state.delete("k")
        assert state.get("k") is None

    def test_delete_missing_key_noop(self) -> None:
        state = _make_state()
        state.delete("missing")
        events = state.pull_events()
        assert len(events) == 0


class TestGraphExecutionStateInputPatch:
    def test_patch_updates_multiple_keys(self) -> None:
        state = _make_state()
        state.patch({"a": 1, "b": 2})
        assert state.get("a") == 1
        assert state.get("b") == 2
        assert len(state.pull_events()) == 2


class TestGraphExecutionStateInputSupersede:
    def test_supersede_flags_not_current(self) -> None:
        state = _make_state()
        assert state.is_current is True
        state.supersede()
        assert state.is_current is False


class TestGraphExecutionStateInputSnapshot:
    def test_snapshot_returns_copy(self) -> None:
        state = _make_state()
        state.update("k", "v")
        snap = state.snapshot()
        assert snap == {"k": "v"}
        snap["k"] = "changed"
        assert state.get("k") == "v"


class TestGraphExecutionStateInputClear:
    def test_clear_removes_all_keys(self) -> None:
        state = _make_state()
        state.update("a", 1)
        state.update("b", 2)
        state.clear()
        assert state.state_data == {}
        assert len(state.pull_events()) == 4
