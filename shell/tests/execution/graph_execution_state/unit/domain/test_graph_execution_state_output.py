from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_execution_state.events.graph_execution_state_changed_event import (
    GraphExecutionStateChangedEvent,
)
from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.types import JsonStr

_NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
_GE_ID = GraphExecutionId("ge-1")


def _make_state() -> GraphExecutionState:
    return GraphExecutionState.create(
        id_=GraphExecutionStateId.generate(),
        graph_execution_id=_GE_ID,
        direction=StateDirection.OUT,
        now=CreatedAt.from_datetime(_NOW),
    )


def _parse(sd: StateData) -> dict:
    return json.loads(sd.value.value)


class TestGraphExecutionStateOutputCreate:
    def test_create_has_empty_state(self) -> None:
        state = _make_state()
        assert _parse(state.state_data) == {}
        assert state.graph_execution_id == _GE_ID

    def test_create_with_initial_data(self) -> None:
        state = GraphExecutionState(
            id=GraphExecutionStateId.generate(),
            graph_execution_id=_GE_ID,
            direction=StateDirection.OUT,
            state_data=StateData(JsonStr('{"k": "v"}')),
            created_at=CreatedAt.from_datetime(_NOW),
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
        assert isinstance(event, GraphExecutionStateChangedEvent)
        assert event.key.value == "k"
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
        state.patch(JsonStr('{"a": 1, "b": 2}'))
        assert state.get("a") == 1
        assert state.get("b") == 2
        assert len(state.pull_events()) == 2


class TestGraphExecutionStateOutputMerge:
    def test_merge_adds_new_keys(self) -> None:
        state = _make_state()
        state.update("x", 1)
        child = GraphExecutionState.create(
            id_=GraphExecutionStateId.generate(),
            graph_execution_id=GraphExecutionId("child"),
            direction=StateDirection.OUT,
            now=CreatedAt.from_datetime(_NOW),
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


class TestGraphExecutionStateOutputSnapshot:
    def test_snapshot_returns_copy(self) -> None:
        state = _make_state()
        state.update("k", "v")
        snap = state.snapshot()
        assert _parse(snap) == {"k": "v"}


class TestGraphExecutionStateOutputClear:
    def test_clear_removes_all_keys(self) -> None:
        state = _make_state()
        state.update("a", 1)
        state.update("b", 2)
        state.clear()
        assert _parse(state.state_data) == {}
        assert len(state.pull_events()) == 4
