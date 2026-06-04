from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _close_session(backend: SqlMemoryBackend, session_id: str, status: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    backend.driver_.execute(
        "UPDATE session SET status = ?, ended_at = ? WHERE session_id = ?",
        (status, now, session_id),
    )
    backend.driver_.commit()
