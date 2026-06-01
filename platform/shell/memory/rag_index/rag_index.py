"""rag_index.py
RagIndex — RAG facade: chunk text, embed, persist, retrieve.

Slots:
    _backend  — MemoryBackend instance for persistence
    _embedder — Embedder instance for vector generation
"""

from __future__ import annotations

from shell.memory.memory_backend.memory_backend import MemoryBackend
from shell.memory.rag_index.embedder.embedder import Embedder
from shell.memory.rag_index.internal._chunk_text import _chunk_text
from shell.memory.rag_index.internal._encode_vector import _encode_vector
from shell.memory.rag_index.internal._index_text import _index_text
from shell.memory.rag_index.internal._search import _search


class RagIndex:
    """RAG indexing and retrieval facade.

    Slots:
        _backend  — MemoryBackend instance for persistence
        _embedder — Embedder instance for vector generation
    """

    __slots__ = ("_backend", "_embedder")

    def __init__(self, backend: MemoryBackend, embedder: Embedder) -> None:
        self._backend: MemoryBackend = backend
        self._embedder: Embedder = embedder

    @property
    def backend_(self) -> MemoryBackend:
        return self._backend

    @property
    def embedder_(self) -> Embedder:
        return self._embedder

    def index_text(
        self,
        source_uri: str,
        title: str,
        domain: str,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> int:
        return _index_text(self, source_uri, title, domain, text, chunk_size, overlap)

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        return _chunk_text(text, chunk_size, overlap)

    def encode_vector(self, vector: list[float]) -> bytes:
        return _encode_vector(vector)

    def search(self, query: str, top_k: int = 5, domain: str | None = None) -> list[dict]:
        return _search(self, query, top_k, domain)
