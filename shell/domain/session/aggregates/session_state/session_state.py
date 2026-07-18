from __future__ import annotations

import json
from typing import TYPE_CHECKING, Self

from shell.domain.session.aggregates.session_state.events.session_state_changed_event import (
    SessionStateChangedEvent,
)
from shell.domain.session.aggregates.session_state.value_objects.session_state_id import (
    SessionStateId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from session.aggregates.session_state.events.sessionstate_updated_event import SessionStateUpdatedEvent
from session.aggregates.session_state.events.sessionstate_deleted_event import SessionStateDeletedEvent

from shell.platform.domain.value_objects.deletedat import DeletedAt

from shell.platform.domain.value_objects.updatedat import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.state_direction import StateDirection


class SessionState(AggregateRoot[SessionStateId]):
    __slots__ = (
        "_updated_at","_session_id", "_direction", "_state_data", "_created_at")

    _session_id: SessionId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt

    def __init__(
        self,
        id: SessionStateId,
        session_id: SessionId,
        state_data: StateData,
        created_at: CreatedAt,
        direction: StateDirection,
    ) -> None:
        super().__init__(id)
        self._session_id = session_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: SessionStateId,
        session_id: SessionId,
        state_data: StateData,
        created_at: CreatedAt,
        direction: StateDirection,
    ) -> Self:
        return cls(
            id=id,
            session_id=session_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
        )


    @classmethod
    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            SessionStateUpdatedEvent.now(
                sessionstate_id=self._id,
                now=now,
            )
        )


    @classmethod
    def _new(cls) -> SessionState:
        raise NotImplementedError("_new() not yet implemented")

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            SessionStateDeletedEvent.now(
                sessionstate_id=self._id,
                now=now,
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            SessionStateUpdatedEvent.now(
                sessionstate_id=self._id,
                now=now,
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
    def create(
        cls,
        *,
        id_: SessionStateId,
        session_id: SessionId,
        direction: StateDirection,
        now: CreatedAt,
    ) -> SessionState:
        instance = cls(
            id=id_,
            session_id=session_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=now,
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
                SessionStateChangedEvent.now(
                    session_id=self._session_id,
                    session_state_id=self.id,
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

    def snapshot(self) -> StateData:
        return self._state_data
