from __future__ import annotations

from typing import Protocol

from shell.application.platform.dto import (
    SessionDto,  # noqa: TC002 — SessionDto używany jako typ zwracany w sygnaturze Protocol
)


class SessionQueryService(Protocol):
    """Port do pobierania historii sesji/czatu."""

    async def get_session_history(self, session_id: str) -> SessionDto | None: ...
