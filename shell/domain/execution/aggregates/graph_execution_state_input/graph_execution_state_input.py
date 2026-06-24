"""GraphExecutionStateInput — external input state for a graph execution, a separate AggregateRoot.

This aggregate provides a key-value store (JSONB-backed) scoped to a single
graph_execution_id.  It is *not* owned by GraphExecution — both are peers,
each with its own transactional boundary.

Input state represents data fed into the graph from external sources (other graphs,
external systems).  The graph's own nodes may read this data but are not intended
to modify it — mutations come from outside callers.

Lifecycle:
    1. Created when a GraphExecution receives input from external actors.
    2. Mutated by external callers via `.update(key, value)`.
       Each mutation appends a :class:`GraphExecutionStateInputChangedEvent`.
    3. Superseded on change (previous row marked is_current=False, new row inserted)
       — the ORM table enforces at most one is_current row per graph_execution_id.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution_state_input.events.graph_execution_state_input_changed_event import (
    GraphExecutionStateInputChangedEvent,
)
from shell.domain.platform.base import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state_input.value_objects.graph_execution_state_input_id import (
        GraphExecutionStateInputId,
    )


class GraphExecutionStateInput(AggregateRoot["GraphExecutionStateInputId"]):
    """Aggregate that holds externally-supplied mutable key-value state for one graph execution."""

    __slots__ = (
        "_graph_execution_id",
        "_state_data",
        "_is_current",
        "_created_at",
    )

    _graph_execution_id: GraphExecutionId
    _state_data: dict[str, object]
    _is_current: bool
    _created_at: datetime

    def __init__(
        self,
        id: GraphExecutionStateInputId,
        graph_execution_id: GraphExecutionId,
        state_data: dict[str, object] | None = None,
        is_current: bool = True,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(id)
        self._graph_execution_id = graph_execution_id
        self._state_data = dict(state_data) if state_data else {}
        self._is_current = is_current
        if created_at is not None:
            self._created_at = created_at

    # ------------------------------------------------------------------ properties

    @property
    def graph_execution_id(self) -> GraphExecutionId:
        return self._graph_execution_id

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
        id_: GraphExecutionStateInputId,
        graph_execution_id: GraphExecutionId,
        now: datetime,
    ) -> GraphExecutionStateInput:
        instance = cls(
            id=id_,
            graph_execution_id=graph_execution_id,
            state_data={},
            is_current=True,
            created_at=now,
        )
        instance._created_at = now
        return instance

    # ------------------------------------------------------------------ mutations

    def update(self, key: str, value: object) -> None:
        """Set or overwrite a key. Emits a GraphExecutionStateInputChangedEvent."""
        old_value = self._state_data.get(key)
        self._state_data[key] = value
        self.append_event(
            GraphExecutionStateInputChangedEvent.now(
                graph_execution_id=self._graph_execution_id,
                graph_execution_state_input_id=self.id,
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
                GraphExecutionStateInputChangedEvent.now(
                    graph_execution_id=self._graph_execution_id,
                    graph_execution_state_input_id=self.id,
                    key=key,
                    old_value=old_value,
                    new_value=None,
                    now=self._created_at,
                )
            )

    def patch(self, data: dict[str, object]) -> None:
        """Batch-update multiple keys at once. One event per changed key."""
        for key, value in data.items():
            self.update(key, value)

    def clear(self) -> None:
        keys = list(self._state_data.keys())
        for key in keys:
            self.delete(key)

    def snapshot(self) -> dict[str, object]:
        return dict(self._state_data)

    def supersede(self) -> None:
        self._is_current = False
