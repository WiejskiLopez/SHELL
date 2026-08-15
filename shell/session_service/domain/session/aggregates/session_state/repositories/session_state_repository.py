from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.exists_result import ExistsResult
    from shell.platform.domain.value_objects.state_direction import StateDirection
    from shell.session_service.domain.session.aggregates.session.value_objects.session_id import (
        SessionId,
    )
    from shell.session_service.domain.session.aggregates.session_state.session_state import (
        SessionState,
    )
    from shell.session_service.domain.session.aggregates.session_state.value_objects.session_state_id import (
        SessionStateId,
    )


class SessionStateRepository(Protocol):
    async def get_by_id(self, id_: SessionStateId) -> SessionState | None: ...

    async def list_by_session_id(self, session_id: SessionId) -> list[SessionState]: ...

    async def list_by_session_and_direction(
        self, session_id: SessionId, direction: StateDirection
    ) -> list[SessionState]: ...

    async def save(self, session_state: SessionState) -> None: ...

    async def delete(self, id_: SessionStateId) -> None: ...

    async def exists(self, id_: SessionStateId) -> ExistsResult: ...
