"""GraphExecutionState — external input/output state for a graph execution, a separate AggregateRoot.

Consolidates GraphExecutionStateInput and GraphExecutionStateOutput into a single aggregate
with a ``direction`` discriminator (StateDirection.IN or StateDirection.OUT).

INPUT state represents data fed into the graph from external sources.
OUTPUT state represents data produced by the graph's own nodes during execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.execution_service.domain.execution.aggregates.graph_execution_state.events.graph_execution_state_changed_event import (
    GraphExecutionStateChangedEvent,
)
from shell.execution_service.domain.execution.aggregates.graph_execution_state.events.graph_execution_state_deleted_event import (
    GraphExecutionStateDeletedEvent,
)
from shell.execution_service.domain.execution.aggregates.graph_execution_state.events.graph_execution_state_updated_event import (
    GraphExecutionStateUpdatedEvent,
)
from shell.execution_service.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.updated_at import NONE_UPDATED_AT, UpdatedAt
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.platform.domain.value_objects.state_direction import StateDirection


class GraphExecutionState(AggregateRoot[GraphExecutionStateId]):
    """Aggregate that holds mutable key-value state for one graph execution, discriminated by kind."""

    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
        "_graph_execution_id",
        "_direction",
        "_state_data",
    )

    _graph_execution_id: GraphExecutionId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt
    _updated_at: UpdatedAt
    _deleted_at: DeletedAt

    def __init__(
        self,
        id: GraphExecutionStateId,
        created_at: CreatedAt,
        graph_execution_id: GraphExecutionId,
        direction: StateDirection,
        state_data: StateData,
    ) -> None:
        super().__init__(id)
        self._graph_execution_id = graph_execution_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at
        self._updated_at = NONE_UPDATED_AT
        self._deleted_at = NONE_DELETED_AT

    @classmethod
    def create(
        cls,
        *,
        id_: GraphExecutionStateId,
        now: CreatedAt,
        graph_execution_id: GraphExecutionId,
        direction: StateDirection,
    ) -> GraphExecutionState:
        return cls._new(
            id_=id_,
            graph_execution_id=graph_execution_id,
            direction=direction,
            now=OccurredAt.from_datetime(now.value),
        )

    # ------------------------------------------------------------------ mutations

    def snapshot(self) -> StateData:
        return self._state_data

    @classmethod
    def restore(
        cls,
        id: GraphExecutionStateId,
        created_at: CreatedAt,
        graph_execution_id: GraphExecutionId,
        direction: StateDirection,
        state_data: StateData,
    ) -> Self:
        return cls(
            id=id,
            graph_execution_id=graph_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            GraphExecutionStateUpdatedEvent.now(
                graph_execution_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            GraphExecutionStateDeletedEvent.now(
                graph_execution_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

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
    def _new(
        cls,
        *,
        id_: GraphExecutionStateId,
        now: OccurredAt,
        graph_execution_id: GraphExecutionId,
        direction: StateDirection,
    ) -> GraphExecutionState:
        instance = cls(
            id=id_,
            graph_execution_id=graph_execution_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            GraphExecutionStateChangedEvent.now(
                graph_execution_id=graph_execution_id,
                graph_execution_state_id=instance.id,
                now=now,
            )
        )
        return instance
