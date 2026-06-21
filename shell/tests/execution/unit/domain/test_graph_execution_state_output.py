from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.graph_execution_state_output.graph_execution_state_output import (
    GraphExecutionStateOutput,
)
from shell.domain.execution.aggregates.graph_execution_state_output.events.graph_execution_state_output_changed_event import (
    GraphExecutionStateOutputChangedEvent,
)
from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphExecutionStateOutputId

_NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
_GE_ID = GraphExecutionId("ge-1")


def _make_state(state_data: dict[str, object] | None = None) -> GraphExecutionStateOutput:
    return GraphExecutionStateOutput.create(
        id_=GraphExecutionStateOutputId.generate(),
        graph_execution_id=_GE_ID,
        now=_NOW,
    )


class TestGraphExecutionStateOutputCreate:
    def test_create_has_empty_state(self) -> None:
        state = _make_state()
        assert state.state_data == {}
        assert state.is_current is True
        assert state.graph_execution_id == _GE_ID

    def test_create_with_initial_data(self) -> None:
        state = GraphExecutionStateOutput(
            id=GraphExecutionStateOutputId.generate(),
            graph_execution_id=_GE_ID,
            state_data={"k": "v"},
            is_current=True,
            created_at=_NOW,
        )
        assert state.get("k") == "v"


class TestGraphExecutionStateOutputUpdate:
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
        assert isinstance(event, GraphExecutionStateOutputChangedEvent)
        assert event.key == "k"
        assert event.old_value is None
        assert event.new_value == "v"


class TestGraphExecutionStateOutputDelete:
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


class TestGraphExecutionStateOutputPatch:
    def test_patch_updates_multiple_keys(self) -> None:
        state = _make_state()
        state.patch({"a": 1, "b": 2})
        assert state.get("a") == 1
        assert state.get("b") == 2
        assert len(state.pull_events()) == 2


class TestGraphExecutionStateOutputMerge:
    def test_merge_adds_new_keys(self) -> None:
        state = _make_state()
        state.update("x", 1)
        child = GraphExecutionStateOutput.create(
            id_=GraphExecutionStateOutputId.generate(),
            graph_execution_id=GraphExecutionId("child"),
            now=_NOW,
        )
        child.update("y", 2)
        child.update("x", 999)
        state.merge(child)
        assert state.get("x") == 1
        assert state.get("y") == 2

    def test_merge_empty_other_noop(self) -> None:
        state = _make_state()
        state.update("x", 1)
        other = _make_state()
        state.merge(other)
        assert state.get("x") == 1


class TestGraphExecutionStateOutputSupersede:
    def test_supersede_flags_not_current(self) -> None:
        state = _make_state()
        assert state.is_current is True
        state.supersede()
        assert state.is_current is False


class TestGraphExecutionStateOutputSnapshot:
    def test_snapshot_returns_copy(self) -> None:
        state = _make_state()
        state.update("k", "v")
        snap = state.snapshot()
        assert snap == {"k": "v"}
        snap["k"] = "changed"
        assert state.get("k") == "v"


class TestGraphExecutionStateOutputClear:
    def test_clear_removes_all_keys(self) -> None:
        state = _make_state()
        state.update("a", 1)
        state.update("b", 2)
        state.clear()
        assert state.state_data == {}
        assert len(state.pull_events()) == 4
