from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution.value_objects.session_snapshot import (
        SessionSnapshot,
    )


class SessionQueryProvider(Protocol):
    """Port owned by the execution BC to fetch session data from the session BC."""

    async def get_by_id(self, session_id: str) -> SessionSnapshot | None: ...
