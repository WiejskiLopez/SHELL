from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime
from shell.session_service.domain.session.aggregates.session_state.events.session_state_changed_event import (
    SessionStateChangedEvent,
)
from shell.session_service.domain.session.aggregates.session_state.events.session_state_created_event import (
    SessionStateCreatedEvent,
)
from shell.session_service.domain.session.aggregates.session_state.events.session_state_deleted_event import (
    SessionStateDeletedEvent,
)
from shell.session_service.domain.session.aggregates.session_state.value_objects.session_state_id import (
    SessionStateId,
)

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.state_direction import StateDirection
    from shell.session_service.domain.session.aggregates.session.value_objects.session_id import (
        SessionId,
    )


class SessionState(AggregateRoot[SessionStateId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_session_id",
        "_direction",
        "_state_data",
    )

    _session_id: SessionId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt
    _changed_at: ChangedAt

    def __init__(
        self,
        *,
        id: SessionStateId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        session_id: SessionId,
        direction: StateDirection,
        state_data: StateData,
    ) -> None:
        super().__init__(id)
        self._session_id = session_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at

    @classmethod
    def create(
        cls,
        *,
        id_: SessionStateId,
        now: CreatedAt,
        session_id: SessionId,
        direction: StateDirection,
    ) -> SessionState:
        return cls._new(
            id_=id_,
            session_id=session_id,
            direction=direction,
            now=OccurredAt.from_datetime(now.value),
        )

    def change_state(self, state_data: StateData) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Cannot change state of a deleted session state")
        self._state_data = state_data
        self._change(now=OccurredAt.from_datetime(self._created_at.value))

    def snapshot(self) -> StateData:
        return self._state_data

    @classmethod
    def restore(
        cls,
        *,
        id: SessionStateId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        session_id: SessionId,
        direction: StateDirection,
        state_data: StateData,
    ) -> Self:
        return cls(
            id=id,
            session_id=session_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SessionStateChangedEvent.now(
                session_id=self._session_id,
                session_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SessionStateDeletedEvent.now(
                session_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def session_id(self) -> SessionId:
        return self._session_id

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
        id_: SessionStateId,
        now: OccurredAt,
        session_id: SessionId,
        direction: StateDirection,
    ) -> SessionState:
        instance = cls(
            id=id_,
            session_id=session_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            SessionStateCreatedEvent.now(
                session_id=session_id,
                session_state_id=id_,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance
