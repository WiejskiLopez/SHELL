from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.aggregates.session_state.repositories.session_state_repository import (
    SessionStateRepository,
)
from shell.domain.session.aggregates.session_state.value_objects.session_state_id import (
    SessionStateId,
)
from shell.domain.execution.value_objects.state_kind import StateKind

if TYPE_CHECKING:
    from shell.domain.session.aggregates.session_state.session_state import SessionState


class InMemorySessionStateRepository(SessionStateRepository):
    def __init__(self) -> None:
        self._store: dict[str, SessionState] = {}

    async def get_by_id(self, id_: SessionStateId) -> SessionState | None:
        item = self._store.get(id_.value)
        return copy.deepcopy(item) if item is not None else None

    async def list_by_session_id(self, session_id: SessionId) -> list[SessionState]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.session_id == session_id
        ]

    async def list_by_session_and_kind(
        self, session_id: SessionId, kind: StateKind
    ) -> list[SessionState]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.session_id == session_id and item.kind == kind
        ]

    async def save(self, session_state: SessionState) -> None:
        self._store[session_state.id.value] = copy.deepcopy(session_state)

    async def delete(self, id_: SessionStateId) -> None:
        self._store.pop(id_.value, None)

    async def exists(self, id_: SessionStateId) -> bool:
        return id_.value in self._store
