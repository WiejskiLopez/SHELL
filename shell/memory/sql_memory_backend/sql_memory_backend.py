"""sql_memory_backend.py
SqlMemoryBackend — SQL-based MemoryBackend that uses any SqlDriver (bridge).

Wymiana bazy = wstrzyknięcie innego drivera w konstruktorze.

Slots:
    _driver — SqlDriver instance (sqlite/postgres/...)
"""

from __future__ import annotations

from shell.memory.memory_backend.memory_backend import MemoryBackend
from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.memory.sql_memory_backend.internal._init_sql_memory_backend import _init_sql_memory_backend
from shell.memory.sql_memory_backend.internal._close_sql_memory_backend import _close_sql_memory_backend
from shell.memory.sql_memory_backend.internal._put_entry import _put_entry
from shell.memory.sql_memory_backend.internal._get_entry import _get_entry
from shell.memory.sql_memory_backend.internal._list_entries import _list_entries
from shell.memory.sql_memory_backend.internal._delete_entry import _delete_entry
from shell.memory.sql_memory_backend.internal._open_session import _open_session
from shell.memory.sql_memory_backend.internal._close_session import _close_session
from shell.memory.sql_memory_backend.internal._append_message import _append_message
from shell.memory.sql_memory_backend.internal._get_conversation import _get_conversation
from shell.memory.sql_memory_backend.internal._log_event import _log_event
from shell.memory.sql_memory_backend.internal._index_document import _index_document
from shell.memory.sql_memory_backend.internal._search_rag import _search_rag
from shell.memory.sql_memory_backend.internal._search_fts import _search_fts


class SqlMemoryBackend(MemoryBackend):
    """SQL-based MemoryBackend powered by a pluggable SqlDriver."""

    __slots__ = ("_driver",)

    def __init__(self, driver: SqlDriver) -> None:
        self._driver: SqlDriver = driver

    @property
    def driver_(self) -> SqlDriver:
        return self._driver

    def init_backend(self) -> None:
        _init_sql_memory_backend(self)

    def close_backend(self) -> None:
        _close_sql_memory_backend(self)

    def put_entry(self, context_type, scope_id, entry_key, value, tags=None):
        _put_entry(self, context_type, scope_id, entry_key, value, tags)

    def get_entry(self, context_type, scope_id, entry_key):
        return _get_entry(self, context_type, scope_id, entry_key)

    def list_entries(self, context_type, scope_id):
        return _list_entries(self, context_type, scope_id)

    def delete_entry(self, context_type, scope_id, entry_key):
        _delete_entry(self, context_type, scope_id, entry_key)

    def open_session(self, session_id, agent_id, goal):
        _open_session(self, session_id, agent_id, goal)

    def close_session(self, session_id, status):
        _close_session(self, session_id, status)

    def append_message(self, correlation_id, sender, receiver, payload):
        _append_message(self, correlation_id, sender, receiver, payload)

    def get_conversation(self, correlation_id):
        return _get_conversation(self, correlation_id)

    def log_event(self, request_id, event_type, payload, trace_id=None, user=None):
        _log_event(self, request_id, event_type, payload, trace_id, user)

    def index_document(self, source_uri, title, domain, chunks, embeddings, embedding_model):
        return _index_document(self, source_uri, title, domain, chunks, embeddings, embedding_model)

    def search_rag(self, query_embedding, top_k=5, domain=None):
        return _search_rag(self, query_embedding, top_k, domain)

    def search_fts(self, query_text, top_k=5):
        return _search_fts(self, query_text, top_k)
