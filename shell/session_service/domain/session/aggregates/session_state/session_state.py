from __future__ import annotations

import json
from typing import TYPE_CHECKING, Self

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.updated_at import NONE_UPDATED_AT, UpdatedAt
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime
from shell.session_service.domain.session.aggregates.session_state.events.session_state_changed_event import (
    SessionStateChangedEvent,
)
from shell.session_service.domain.session.aggregates.session_state.events.session_state_deleted_event import (
    SessionStateDeletedEvent,
)
from shell.session_service.domain.session.aggregates.session_state.events.session_state_updated_event import (
    SessionStateUpdatedEvent,
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
        "_updated_at",
        "_deleted_at",
        "_session_id",
        "_direction",
        "_state_data",
    )

    _session_id: SessionId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt

    def __init__(
        self,
        *,
        id: SessionStateId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
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
        self._updated_at = updated_at
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
        instance = cls(
            id=id_,
            session_id=session_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=CreatedAt.from_datetime(now.value),
        )
        return instance

    def update(self, key: str, value: object) -> None:
        new_data = json.loads(self._state_data.value.value)
        new_data[key] = value
        self._state_data = StateData(JsonStr(json.dumps(new_data)))
        self.append_event(
            SessionStateChangedEvent.now(
                session_id=self._session_id,
                session_state_id=self.id,
                now=OccurredAt.from_datetime(self._created_at.value),
            )
        )

    def get(self, key: str) -> object | None:
        return json.loads(self._state_data.value.value).get(key)  # type: ignore[no-any-return]

    def _remove_key(self, key: str) -> None:
        if json.loads(self._state_data.value.value).get(key) is not None:
            new_data = json.loads(self._state_data.value.value)
            new_data.pop(key, None)
            self._state_data = StateData(JsonStr(json.dumps(new_data)))
            self.append_event(
                SessionStateChangedEvent.now(
                    session_id=self._session_id,
                    session_state_id=self.id,
                    now=OccurredAt.from_datetime(self._created_at.value),
                )
            )

    def patch(self, data: JsonStr) -> None:
        parsed = json.loads(data.value)
        for key, value in parsed.items():
            self.update(key, value)

    def clear(self) -> None:
        current = json.loads(self._state_data.value.value)
        for key in list(current.keys()):
            self._remove_key(key)

    def snapshot(self) -> StateData:
        return self._state_data

    @classmethod
    def restore(
        cls,
        *,
        id: SessionStateId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
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
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            SessionStateUpdatedEvent.now(
                session_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
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
        return instance
