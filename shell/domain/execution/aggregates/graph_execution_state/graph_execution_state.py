"""GraphExecutionState — external input/output state for a graph execution, a separate AggregateRoot.

Consolidates GraphExecutionStateInput and GraphExecutionStateOutput into a single aggregate
with a ``direction`` discriminator (StateDirection.IN or StateDirection.OUT).

INPUT state represents data fed into the graph from external sources.
OUTPUT state represents data produced by the graph's own nodes during execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from shell.domain.execution.aggregates.graph_execution_state.events.graph_execution_state_changed_event import (
    GraphExecutionStateChangedEvent,
)
from shell.domain.execution.value_objects.state_key import StateKey
from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt


class GraphExecutionState(AggregateRoot["GraphExecutionStateId"]):
    """Aggregate that holds mutable key-value state for one graph execution, discriminated by kind."""

    __slots__ = (
        "_graph_execution_id",
        "_direction",
        "_state_data",
        "_created_at",
    )

    _graph_execution_id: GraphExecutionId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt

    def __init__(
        self,
        id: GraphExecutionStateId,
        graph_execution_id: GraphExecutionId,
        direction: StateDirection,
        state_data: StateData | None = None,
        created_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._graph_execution_id = graph_execution_id
        self._direction = direction
        self._state_data = state_data or StateData({})
        if created_at is not None:
            self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: GraphExecutionStateId,
        graph_execution_id: GraphExecutionId,
        direction: StateDirection,
        state_data: StateData | None = None,
        created_at: CreatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            graph_execution_id=graph_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
        )

    # ------------------------------------------------------------------ properties

    @property
    def graph_execution_id(self) -> GraphExecutionId:
        return self._graph_execution_id

    @property
    def direction(self) -> StateDirection:
        return self._direction

    @property
    def state_data(self) -> dict[str, Any]:
        return self._state_data.to_dict().copy()

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    # ------------------------------------------------------------------ factory

    @classmethod
    def create(
        cls,
        *,
        id_: GraphExecutionStateId,
        graph_execution_id: GraphExecutionId,
        direction: StateDirection = StateDirection.IN,
        now: CreatedAt,
    ) -> GraphExecutionState:
        return cls(
            id=id_,
            graph_execution_id=graph_execution_id,
            direction=direction,
            state_data=StateData({}),
            created_at=now,
        )

    # ------------------------------------------------------------------ mutations

    def update(self, key: str, value: object) -> None:
        old_value = self._state_data.get(key)
        new_data = dict(self._state_data.to_dict())
        new_data[key] = value
        self._state_data = StateData(new_data)
        self.append_event(
            GraphExecutionStateChangedEvent.now(
                graph_execution_id=self._graph_execution_id,
                graph_execution_state_id=self.id,
                direction=self._direction,
                key=StateKey(key),
                old_value=old_value,
                new_value=value,
                now=self._created_at,
            )
        )

    def get(self, key: str) -> object | None:
        return self._state_data.get(key)  # type: ignore[no-any-return]

    def delete(self, key: str) -> None:
        if self._state_data.get(key) is not None:
            old_value = self._state_data.get(key)
            new_data = dict(self._state_data.to_dict())
            new_data.pop(key, None)
            self._state_data = StateData(new_data)
            self.append_event(
                GraphExecutionStateChangedEvent.now(
                    graph_execution_id=self._graph_execution_id,
                    graph_execution_state_id=self.id,
                    direction=self._direction,
                    key=StateKey(key),
                    old_value=old_value,
                    new_value=None,
                    now=self._created_at,
                )
            )

    def patch(self, data: dict[str, object]) -> None:
        for key, value in data.items():
            self.update(key, value)

    def clear(self) -> None:
        current = self._state_data.to_dict()
        for key in list(current.keys()):
            self.delete(key)

    def merge(self, other: GraphExecutionState) -> None:
        """Incorporate state from a child task (Tasker pattern).

        Keys present in *other* but absent in *self* are copied.
        Keys already present in *self* are left unchanged (parent wins).
        """
        other_data = other._state_data.to_dict()
        current = self._state_data.to_dict()
        for key, value in other_data.items():
            if key not in current:
                self.update(key, value)

    def snapshot(self) -> dict[str, Any]:
        return self._state_data.to_dict().copy()


