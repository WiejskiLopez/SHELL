from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _open_session(backend: SqlMemoryBackend, session_id: str, agent_id: str, goal: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    backend.driver_.execute(
        """
        INSERT INTO session (session_id, agent_id, goal, status, started_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            agent_id = excluded.agent_id,
            goal     = excluded.goal,
            status   = excluded.status,
            started_at = excluded.started_at
        """,
        (session_id, agent_id, goal, "active", now),
    )
    backend.driver_.commit()
