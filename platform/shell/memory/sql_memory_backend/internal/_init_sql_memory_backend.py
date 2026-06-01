from __future__ import annotations

from typing import TYPE_CHECKING

from shell.memory.sql_memory_backend.internal._apply_schema import _apply_schema

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _init_sql_memory_backend(backend: SqlMemoryBackend) -> None:
    backend.driver_.connect()
    _apply_schema(backend)
