from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _delete_entry(backend: SqlMemoryBackend, context_type: str, scope_id: str, entry_key: str) -> None:
    backend.driver_.execute(
        "DELETE FROM context_entry WHERE context_type = ? AND scope_id = ? AND entry_key = ?",
        (context_type, scope_id, entry_key),
    )
    backend.driver_.commit()
