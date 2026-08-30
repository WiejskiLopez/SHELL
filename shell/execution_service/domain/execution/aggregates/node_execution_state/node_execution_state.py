from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.execution_service.domain.execution.aggregates.node_execution_state.events.node_execution_state_changed_event import (
    NodeExecutionStateChangedEvent,
)
from shell.execution_service.domain.execution.aggregates.node_execution_state.events.node_execution_state_created_event import (
    NodeExecutionStateCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.node_execution_state.events.node_execution_state_deleted_event import (
    NodeExecutionStateDeletedEvent,
)
from shell.execution_service.domain.execution.aggregates.node_execution_state.value_objects.node_execution_state_id import (
    NodeExecutionStateId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.deleted_at import DeletedAt
    from shell.platform.domain.value_objects.state_direction import StateDirection


class NodeExecutionState(AggregateRoot[NodeExecutionStateId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_node_execution_id",
        "_direction",
        "_state_data",
    )

    _node_execution_id: NodeExecutionId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt
    _changed_at: ChangedAt
    _deleted_at: DeletedAt

    def __init__(
        self,
        id: NodeExecutionStateId,
        created_at: CreatedAt,
        node_execution_id: NodeExecutionId,
        direction: StateDirection,
        state_data: StateData,
    ) -> None:
        super().__init__(id)
        self._node_execution_id = node_execution_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at
        self._changed_at = NONE_CHANGED_AT
        self._deleted_at = NONE_DELETED_AT

    @classmethod
    def create(
        cls,
        *,
        id_: NodeExecutionStateId,
        now: CreatedAt,
        node_execution_id: NodeExecutionId,
        direction: StateDirection,
    ) -> NodeExecutionState:
        return cls._new(
            id_=id_,
            node_execution_id=node_execution_id,
            direction=direction,
            now=OccurredAt.from_datetime(now.value),
        )

    def change_state(self, state_data: StateData, now: OccurredAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Cannot change state of a deleted node execution state")
        self._state_data = state_data
        self._change(now=now)

    def snapshot(self) -> StateData:
        return self._state_data

    @classmethod
    def restore(
        cls,
        id: NodeExecutionStateId,
        created_at: CreatedAt,
        node_execution_id: NodeExecutionId,
        direction: StateDirection,
        state_data: StateData,
    ) -> Self:
        return cls(
            id=id,
            node_execution_id=node_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            NodeExecutionStateChangedEvent.now(
                node_execution_id=self._node_execution_id,
                node_execution_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            NodeExecutionStateDeletedEvent.now(
                node_execution_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self._node_execution_id

    @property
    def direction(self) -> StateDirection:
        return self._direction

    @property
    def state_data(self) -> StateData:
        return self._state_data

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @classmethod
    def _new(
        cls,
        *,
        id_: NodeExecutionStateId,
        now: OccurredAt,
        node_execution_id: NodeExecutionId,
        direction: StateDirection,
    ) -> NodeExecutionState:
        instance = cls(
            id=id_,
            node_execution_id=node_execution_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            NodeExecutionStateCreatedEvent.now(
                node_execution_id=node_execution_id,
                node_execution_state_id=id_,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance
