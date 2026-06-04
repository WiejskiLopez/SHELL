"""memory_backend.py
MemoryBackend — abstract interface for persistent memory storage backends.

Slots:
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class MemoryBackend(ABC):
    """Abstract base for memory storage backends.

    Implementations: SqlMemoryBackend (SqliteDriver default; PostgresDriver stub), future: Chroma, Qdrant.
    """

    __slots__ = ()

    @abstractmethod
    def init_backend(self) -> None:
        ...

    @abstractmethod
    def close_backend(self) -> None:
        ...

    @abstractmethod
    def put_entry(self, context_type: str, scope_id: str, entry_key: str, value: dict, tags: list[str] | None = None) -> None:
        ...

    @abstractmethod
    def get_entry(self, context_type: str, scope_id: str, entry_key: str) -> dict | None:
        ...

    @abstractmethod
    def list_entries(self, context_type: str, scope_id: str) -> list[dict]:
        ...

    @abstractmethod
    def delete_entry(self, context_type: str, scope_id: str, entry_key: str) -> None:
        ...

    @abstractmethod
    def open_session(self, session_id: str, agent_id: str, goal: str) -> None:
        ...

    @abstractmethod
    def close_session(self, session_id: str, status: str) -> None:
        ...

    @abstractmethod
    def append_message(self, correlation_id: str, sender: str, receiver: str, payload: dict) -> None:
        ...

    @abstractmethod
    def get_conversation(self, correlation_id: str) -> list[dict]:
        ...

    @abstractmethod
    def log_event(self, request_id: str, event_type: str, payload: dict, trace_id: str | None = None, user: str | None = None) -> None:
        ...

    @abstractmethod
    def index_document(self, source_uri: str, title: str, domain: str, chunks: list[str], embeddings: list[bytes], embedding_model: str) -> int:
        ...

    @abstractmethod
    def search_rag(self, query_embedding: bytes, top_k: int = 5, domain: str | None = None) -> list[dict]:
        ...

    @abstractmethod
    def search_fts(self, query_text: str, top_k: int = 5) -> list[dict]:
        ...
