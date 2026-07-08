from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.session.session_state.dto.session_state import SessionStateDto


class SessionStateQueryService(Protocol):
    async def get_by_id(self, session_state_id: str) -> SessionStateDto | None: ...
