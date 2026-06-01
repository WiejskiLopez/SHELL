from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _get_entry(
    backend: SqlMemoryBackend,
    context_type: str,
    scope_id: str,
    entry_key: str,
) -> dict | None:
    rows = backend.driver_.query(
        """
        SELECT value_json, tags, created_at, updated_at
        FROM context_entry
        WHERE context_type = ? AND scope_id = ? AND entry_key = ?
        """,
        (context_type, scope_id, entry_key),
    )
    if not rows:
        return None
    row = rows[0]
    return {
        "value": json.loads(row["value_json"]),
        "tags": row["tags"].split(",") if row["tags"] else [],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
