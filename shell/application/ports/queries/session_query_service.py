from typing import Protocol

from shell.application.dto.dto import SessionDto


class SessionQueryService(Protocol):
    """Port do pobierania historii sesji/czatu."""

    async def get_session_history(self, session_id: str) -> SessionDto | None: ...
