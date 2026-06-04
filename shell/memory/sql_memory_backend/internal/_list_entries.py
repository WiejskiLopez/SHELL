from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _list_entries(backend: SqlMemoryBackend, context_type: str, scope_id: str) -> list[dict]:
    rows = backend.driver_.query(
        """
        SELECT entry_key, value_json, tags, created_at, updated_at
        FROM context_entry
        WHERE context_type = ? AND scope_id = ?
        ORDER BY entry_key
        """,
        (context_type, scope_id),
    )
    return [
        {
            "entry_key": r["entry_key"],
            "value": json.loads(r["value_json"]),
            "tags": r["tags"].split(",") if r["tags"] else [],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]
