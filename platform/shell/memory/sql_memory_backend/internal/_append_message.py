from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _append_message(
    backend: SqlMemoryBackend,
    correlation_id: str,
    sender: str,
    receiver: str,
    payload: dict,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    backend.driver_.execute(
        """
        INSERT INTO message (correlation_id, sender, receiver, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (correlation_id, sender, receiver, json.dumps(payload, ensure_ascii=False), now),
    )
    backend.driver_.commit()
