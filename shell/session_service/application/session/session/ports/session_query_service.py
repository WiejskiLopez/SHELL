from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.session_service.application.session.session.dto.session import SessionDto


class SessionQueryService(Protocol):
    """Port do pobierania historii sesji/czatu."""

    async def get_by_id(self, session_id: str) -> SessionDto | None: ...

    async def list_all(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
        user_id: str | None = None,
    ) -> tuple[list[SessionDto], int]: ...
