from __future__ import annotations

from typing import Protocol

from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.aggregates.session_state.session_state import SessionState
from shell.domain.session.aggregates.session_state.value_objects.session_state_id import (
    SessionStateId,
)
from shell.domain.execution.value_objects.state_direction import StateDirection
from shell.domain.execution.value_objects.exists_result import ExistsResult


class SessionStateRepository(Protocol):
    async def get_by_id(self, id_: SessionStateId) -> SessionState | None: ...

    async def list_by_session_id(self, session_id: SessionId) -> list[SessionState]: ...

    async def list_by_session_and_direction(
        self, session_id: SessionId, direction: StateDirection
    ) -> list[SessionState]: ...

    async def save(self, session_state: SessionState) -> None: ...

    async def delete(self, id_: SessionStateId) -> None: ...

    async def exists(self, id_: SessionStateId) -> ExistsResult: ...
