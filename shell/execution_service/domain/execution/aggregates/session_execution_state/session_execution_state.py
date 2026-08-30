from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.execution_service.domain.execution.aggregates.session_execution_state.events.session_execution_state_changed_event import (
    SessionExecutionStateChangedEvent,
)
from shell.execution_service.domain.execution.aggregates.session_execution_state.events.session_execution_state_created_event import (
    SessionExecutionStateCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.session_execution_state.events.session_execution_state_deleted_event import (
    SessionExecutionStateDeletedEvent,
)
from shell.execution_service.domain.execution.aggregates.session_execution_state.value_objects.session_execution_state_id import (
    SessionExecutionStateId,
)
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
        SessionExecutionId,
    )
    from shell.platform.domain.value_objects.state_data import StateData
    from shell.platform.domain.value_objects.state_direction import StateDirection


class SessionExecutionState(AggregateRoot[SessionExecutionStateId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_session_execution_id",
        "_direction",
        "_state_data",
    )

    _session_execution_id: SessionExecutionId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt
    _changed_at: ChangedAt
    _deleted_at: DeletedAt

    def __init__(
        self,
        id: SessionExecutionStateId,
        created_at: CreatedAt,
        session_execution_id: SessionExecutionId,
        direction: StateDirection,
        state_data: StateData,
    ) -> None:
        super().__init__(id)
        self._session_execution_id = session_execution_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at
        self._changed_at = NONE_CHANGED_AT
        self._deleted_at = NONE_DELETED_AT

    @classmethod
    def create(
        cls,
        *,
        id_: SessionExecutionStateId,
        now: CreatedAt,
        session_execution_id: SessionExecutionId,
        direction: StateDirection,
        state_data: StateData,
    ) -> SessionExecutionState:
        return cls._new(
            id_=id_,
            session_execution_id=session_execution_id,
            state_data=state_data,
            now=OccurredAt.from_datetime(now.value),
            direction=direction,
        )

    @classmethod
    def restore(
        cls,
        id: SessionExecutionStateId,
        created_at: CreatedAt,
        session_execution_id: SessionExecutionId,
        direction: StateDirection,
        state_data: StateData,
    ) -> Self:
        return cls(
            id=id,
            session_execution_id=session_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SessionExecutionStateDeletedEvent.now(
                session_execution_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SessionExecutionStateChangedEvent.now(
                session_execution_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def session_execution_id(self) -> SessionExecutionId:
        return self._session_execution_id

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
        id_: SessionExecutionStateId,
        now: OccurredAt,
        session_execution_id: SessionExecutionId,
        direction: StateDirection,
        state_data: StateData,
    ) -> SessionExecutionState:
        instance = cls(
            id=id_,
            session_execution_id=session_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            SessionExecutionStateCreatedEvent.now(
                session_execution_state_id=instance.id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance
