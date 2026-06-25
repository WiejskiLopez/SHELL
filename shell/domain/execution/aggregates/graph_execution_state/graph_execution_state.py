"""GraphExecutionState — external input/output state for a graph execution, a separate AggregateRoot.

Consolidates GraphExecutionStateInput and GraphExecutionStateOutput into a single aggregate
with a ``kind`` discriminator (StateKind.INPUT or StateKind.OUTPUT).

INPUT state represents data fed into the graph from external sources.
OUTPUT state represents data produced by the graph's own nodes during execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.graph_execution_state.events.graph_execution_state_changed_event import (
    GraphExecutionStateChangedEvent,
)
from shell.domain.execution.value_objects.state_kind import StateKind
from shell.domain.platform.base import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )


class GraphExecutionState(AggregateRoot["GraphExecutionStateId"]):
    """Aggregate that holds mutable key-value state for one graph execution, discriminated by kind."""

    __slots__ = (
        "_graph_execution_id",
        "_kind",
        "_state_data",
        "_is_current",
        "_created_at",
    )

    _graph_execution_id: GraphExecutionId
    _kind: StateKind
    _state_data: dict[str, object]
    _is_current: bool
    _created_at: datetime

    def __init__(
        self,
        id: GraphExecutionStateId,
        graph_execution_id: GraphExecutionId,
        kind: StateKind = StateKind.INPUT,
        state_data: dict[str, object] | None = None,
        is_current: bool = True,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(id)
        self._graph_execution_id = graph_execution_id
        self._kind = kind
        self._state_data = dict(state_data) if state_data else {}
        self._is_current = is_current
        if created_at is not None:
            self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: GraphExecutionStateId,
        graph_execution_id: GraphExecutionId,
        kind: StateKind = StateKind.INPUT,
        state_data: dict[str, object] | None = None,
        is_current: bool = True,
        created_at: datetime | None = None,
    ) -> Self:
        return cls(
            id=id,
            graph_execution_id=graph_execution_id,
            kind=kind,
            state_data=state_data,
            is_current=is_current,
            created_at=created_at,
        )

    # ------------------------------------------------------------------ properties

    @property
    def graph_execution_id(self) -> GraphExecutionId:
        return self._graph_execution_id

    @property
    def kind(self) -> StateKind:
        return self._kind

    @property
    def state_data(self) -> dict[str, object]:
        return self._state_data

    @property
    def is_current(self) -> bool:
        return self._is_current

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # ------------------------------------------------------------------ factory

    @classmethod
    def create(
        cls,
        *,
        id_: GraphExecutionStateId,
        graph_execution_id: GraphExecutionId,
        kind: StateKind = StateKind.INPUT,
        now: datetime,
    ) -> GraphExecutionState:
        instance = cls(
            id=id_,
            graph_execution_id=graph_execution_id,
            kind=kind,
            state_data={},
            is_current=True,
            created_at=now,
        )
        instance._created_at = now
        return instance

    # ------------------------------------------------------------------ mutations

    def update(self, key: str, value: object) -> None:
        old_value = self._state_data.get(key)
        self._state_data[key] = value
        self.append_event(
            GraphExecutionStateChangedEvent.now(
                graph_execution_id=self._graph_execution_id,
                graph_execution_state_id=self.id,
                kind=self._kind,
                key=key,
                old_value=old_value,
                new_value=value,
                now=self._created_at,
            )
        )

    def get(self, key: str) -> object | None:
        return self._state_data.get(key)

    def delete(self, key: str) -> None:
        if key in self._state_data:
            old_value = self._state_data.pop(key)
            self.append_event(
                GraphExecutionStateChangedEvent.now(
                    graph_execution_id=self._graph_execution_id,
                    graph_execution_state_id=self.id,
                    kind=self._kind,
                    key=key,
                    old_value=old_value,
                    new_value=None,
                    now=self._created_at,
                )
            )

    def patch(self, data: dict[str, object]) -> None:
        for key, value in data.items():
            self.update(key, value)

    def clear(self) -> None:
        keys = list(self._state_data.keys())
        for key in keys:
            self.delete(key)

    def merge(self, other: GraphExecutionState) -> None:
        """Incorporate state from a child task (Tasker pattern).

        Keys present in *other* but absent in *self* are copied.
        Keys already present in *self* are left unchanged (parent wins).
        """
        for key, value in other._state_data.items():
            if key not in self._state_data:
                self.update(key, value)

    def snapshot(self) -> dict[str, object]:
        return dict(self._state_data)

    def supersede(self) -> None:
        self._is_current = False
