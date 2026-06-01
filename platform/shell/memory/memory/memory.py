"""memory.py
Memory — facade exposing the persistent context store and RAG index.

Slots:
    _backend  — Optional; MemoryBackend instance (None until init_memory)
    _rag      — Optional; RagIndex instance (None until init_memory)
"""

from __future__ import annotations

from shell.memory.memory_backend.memory_backend import MemoryBackend
from shell.memory.rag_index.embedder.embedder import Embedder
from shell.memory.rag_index.rag_index import RagIndex
from shell.memory.memory.internal._init_memory import _init_memory


class Memory:
    """Facade exposing the persistent context store and RAG index.

    Slots:
        _backend  — Optional; MemoryBackend instance (None until init_memory)
        _rag      — Optional; RagIndex instance (None until init_memory)
    """

    __slots__ = ("_backend", "_rag")

    def __init__(self) -> None:
        self._backend: MemoryBackend | None = None
        self._rag: RagIndex | None = None

    @property
    def backend_(self) -> MemoryBackend:
        return self._backend

    @property
    def rag_(self) -> RagIndex:
        return self._rag

    def init_memory(self, backend: MemoryBackend, embedder: Embedder | None = None) -> None:
        _init_memory(self, backend, embedder)

    def close_memory(self) -> None:
        if self._backend is not None:
            self._backend.close_backend()

    def put_entry(self, context_type: str, scope_id: str, entry_key: str, value: dict, tags: list[str] | None = None) -> None:
        self._backend.put_entry(context_type, scope_id, entry_key, value, tags)

    def get_entry(self, context_type: str, scope_id: str, entry_key: str) -> dict | None:
        return self._backend.get_entry(context_type, scope_id, entry_key)

    def list_entries(self, context_type: str, scope_id: str) -> list[dict]:
        return self._backend.list_entries(context_type, scope_id)

    def delete_entry(self, context_type: str, scope_id: str, entry_key: str) -> None:
        self._backend.delete_entry(context_type, scope_id, entry_key)

    def open_session(self, session_id: str, agent_id: str, goal: str) -> None:
        self._backend.open_session(session_id, agent_id, goal)

    def close_session(self, session_id: str, status: str) -> None:
        self._backend.close_session(session_id, status)

    def append_message(self, correlation_id: str, sender: str, receiver: str, payload: dict) -> None:
        self._backend.append_message(correlation_id, sender, receiver, payload)

    def get_conversation(self, correlation_id: str) -> list[dict]:
        return self._backend.get_conversation(correlation_id)

    def log_event(self, request_id: str, event_type: str, payload: dict, trace_id: str | None = None, user: str | None = None) -> None:
        self._backend.log_event(request_id, event_type, payload, trace_id, user)

