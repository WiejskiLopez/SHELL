from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _log_event(
    backend: SqlMemoryBackend,
    request_id: str,
    event_type: str,
    payload: dict,
    trace_id: str | None,
    user: str | None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    backend.driver_.execute(
        """
        INSERT INTO audit_event (request_id, trace_id, "user", event_type, payload_json, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (request_id, trace_id, user, event_type, json.dumps(payload, ensure_ascii=False) if payload else None, now),
    )
    backend.driver_.commit()
