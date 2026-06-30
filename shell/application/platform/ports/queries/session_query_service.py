from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.session.dto.session import SessionDto


class SessionQueryService(Protocol):
    async def get_session_history(self, session_id: str) -> SessionDto | None: ...
