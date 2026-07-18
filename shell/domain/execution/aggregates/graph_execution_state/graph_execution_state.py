"""GraphExecutionState — external input/output state for a graph execution, a separate AggregateRoot.

Consolidates GraphExecutionStateInput and GraphExecutionStateOutput into a single aggregate
with a ``direction`` discriminator (StateDirection.IN or StateDirection.OUT).

INPUT state represents data fed into the graph from external sources.
OUTPUT state represents data produced by the graph's own nodes during execution.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.graph_execution_state.events.graph_execution_state_changed_event import (
    GraphExecutionStateChangedEvent,
)
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.state_direction import StateDirection


class GraphExecutionState(AggregateRoot["GraphExecutionStateId"]):
    """Aggregate that holds mutable key-value state for one graph execution, discriminated by kind."""

    __slots__ = (
        "_updated_at",
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
        state_data: StateData,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._graph_execution_id = graph_execution_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: GraphExecutionStateId,
        graph_execution_id: GraphExecutionId,
        direction: StateDirection,
        state_data: StateData,
        created_at: CreatedAt,
    ) -> Self:
        return cls(
            id=id,
            graph_execution_id=graph_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
        )

    # ------------------------------------------------------------------ properties


    @classmethod
    def _update(cls) -> None:
        raise NotImplementedError("_update() not yet implemented")


    @classmethod
    def _new(cls) -> GraphExecutionState:
        raise NotImplementedError("_new() not yet implemented")

    @property
    def graph_execution_id(self) -> GraphExecutionId:
        return self._graph_execution_id

    @property
    def direction(self) -> StateDirection:
        return self._direction

    @property
    def state_data(self) -> StateData:
        return self._state_data

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
        direction: StateDirection,
        now: CreatedAt,
    ) -> GraphExecutionState:
        return cls(
            id=id_,
            graph_execution_id=graph_execution_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=now,
        )

    # ------------------------------------------------------------------ mutations

    def update(self, key: str, value: object) -> None:
        new_data = json.loads(self._state_data.value.value)
        new_data[key] = value
        self._state_data = StateData(JsonStr(json.dumps(new_data)))
        self.append_event(
            GraphExecutionStateChangedEvent.now(
                graph_execution_id=self._graph_execution_id,
                graph_execution_state_id=self.id,
                now=self._created_at,
            )
        )

    def get(self, key: str) -> object | None:
        return json.loads(self._state_data.value.value).get(key)  # type: ignore[no-any-return]

    def _delete(self, key: str) -> None:
        if json.loads(self._state_data.value.value).get(key) is not None:
            new_data = json.loads(self._state_data.value.value)
            new_data.pop(key, None)
            self._state_data = StateData(JsonStr(json.dumps(new_data)))
            self.append_event(
                GraphExecutionStateChangedEvent.now(
                    graph_execution_id=self._graph_execution_id,
                    graph_execution_state_id=self.id,
                    now=self._created_at,
                )
            )

    def patch(self, data: JsonStr) -> None:
        parsed = json.loads(data.value)
        for key, value in parsed.items():
            self.update(key, value)

    def clear(self) -> None:
        current = json.loads(self._state_data.value.value)
        for key in list(current.keys()):
            self.delete(key)

    def merge(self, other: GraphExecutionState) -> None:
        """Incorporate state from a child task (Tasker pattern).

        Keys present in *other* but absent in *self* are copied.
        Keys already present in *self* are left unchanged (parent wins).
        """
        other_data = json.loads(other._state_data.value.value)
        current = json.loads(self._state_data.value.value)
        for key, value in other_data.items():
            if key not in current:
                self.update(key, value)

    def snapshot(self) -> StateData:
        return self._state_data
