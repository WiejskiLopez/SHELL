from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _get_conversation(backend: SqlMemoryBackend, correlation_id: str) -> list[dict]:
    rows = backend.driver_.query(
        """
        SELECT id, sender, receiver, payload_json, created_at
        FROM message
        WHERE correlation_id = ?
        ORDER BY id
        """,
        (correlation_id,),
    )
    return [
        {
            "id": r["id"],
            "sender": r["sender"],
            "receiver": r["receiver"],
            "payload": json.loads(r["payload_json"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]
