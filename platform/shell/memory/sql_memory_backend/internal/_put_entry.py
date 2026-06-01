from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _put_entry(
    backend: SqlMemoryBackend,
    context_type: str,
    scope_id: str,
    entry_key: str,
    value: dict,
    tags: list[str] | None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    tags_csv = ",".join(tags) if tags else None
    value_json = json.dumps(value, ensure_ascii=False)
    backend.driver_.execute(
        """
        INSERT INTO context_entry (context_type, scope_id, entry_key, value_json, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(context_type, scope_id, entry_key) DO UPDATE SET
            value_json = excluded.value_json,
            tags       = excluded.tags,
            updated_at = excluded.updated_at
        """,
        (context_type, scope_id, entry_key, value_json, tags_csv, now, now),
    )
    backend.driver_.commit()
