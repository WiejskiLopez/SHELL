from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository
from shell.session.domain.session.aggregates.session_state.repositories.session_state_repository import (
    SessionStateRepository,
)
from shell.session.domain.session.aggregates.session_state.session_state import SessionState
from shell.session.domain.session.aggregates.session_state.value_objects.session_state_id import (
    SessionStateId,
)

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.state_direction import StateDirection
    from shell.session.domain.session.aggregates.session.value_objects.session_id import SessionId


class InMemorySessionStateRepository(
    InMemoryRepository[SessionState, SessionStateId], SessionStateRepository
):
    async def list_by_session_id(self, session_id: SessionId) -> list[SessionState]:
        return [
            copy.deepcopy(item) for item in self._store.values() if item.session_id == session_id
        ]

    async def list_by_session_and_direction(
        self, session_id: SessionId, direction: StateDirection
    ) -> list[SessionState]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.session_id == session_id and item.direction == direction
        ]

    async def exists(self, id_: SessionStateId) -> ExistsResult:
        return ExistsResult(id_.value in self._store)
