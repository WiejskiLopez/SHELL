from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _close_sql_memory_backend(backend: SqlMemoryBackend) -> None:
    backend.driver_.close()
