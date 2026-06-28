from __future__ import annotations

from typing import Protocol

from shell.application.session.dto.session import SessionDto


class SessionQueryService(Protocol):
    """Port do pobierania historii sesji/czatu."""

    async def get_session_history(self, session_id: str) -> SessionDto | None: ...
