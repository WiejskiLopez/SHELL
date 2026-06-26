from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.aggregates.session_state.events.session_state_changed_event import (
    SessionStateChangedEvent,
)
from shell.domain.session.aggregates.session_state.value_objects.session_state_id import (
    SessionStateId,
)
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.execution.value_objects.state_kind import StateKind
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime


class SessionState(AggregateRoot[SessionStateId]):
    __slots__ = ("_session_id", "_kind", "_state_data", "_created_at")

    _session_id: SessionId
    _kind: StateKind
    _state_data: StateData
    _created_at: CreatedAt

    def __init__(
        self,
        id: SessionStateId,
        session_id: SessionId,
        kind: StateKind = StateKind.INPUT,
        state_data: StateData | None = None,
        created_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._session_id = session_id
        self._kind = kind
        self._state_data = state_data or StateData({})
        if created_at is not None:
            self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: SessionStateId,
        session_id: SessionId,
        kind: StateKind = StateKind.INPUT,
        state_data: StateData | None = None,
        created_at: CreatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            session_id=session_id,
            kind=kind,
            state_data=state_data,
            created_at=created_at,
        )

    @property
    def session_id(self) -> SessionId:
        return self._session_id

    @property
    def kind(self) -> StateKind:
        return self._kind

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
        kind: StateKind = StateKind.INPUT,
        now: datetime,
    ) -> SessionState:
        instance = cls(
            id=id_,
            session_id=session_id,
            kind=kind,
            state_data=StateData({}),
            created_at=now,
        )
        return instance

    def update(self, key: str, value: object) -> None:
        old_value = self._state_data.get(key)
        new_data = dict(self._state_data.to_dict())
        new_data[key] = value
        self._state_data = StateData(new_data)
        self.append_event(
            SessionStateChangedEvent.now(
                session_id=self._session_id,
                session_state_id=self.id,
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
        if self._state_data.get(key) is not None:
            old_value = self._state_data.get(key)
            new_data = dict(self._state_data.to_dict())
            new_data.pop(key, None)
            self._state_data = StateData(new_data)
            self.append_event(
                SessionStateChangedEvent.now(
                    session_id=self._session_id,
                    session_state_id=self.id,
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
        current = self._state_data.to_dict()
        for key in list(current.keys()):
            self.delete(key)

    def snapshot(self) -> StateData:
        return self._state_data
