from __future__ import annotations

from typing import TYPE_CHECKING

from shell.memory.rag_index.rag_index import RagIndex
from shell.memory.rag_index.embedder.hash_embedder import HashEmbedder

if TYPE_CHECKING:
    from shell.memory.memory.memory import Memory
    from shell.memory.memory_backend.memory_backend import MemoryBackend
    from shell.memory.rag_index.embedder.embedder import Embedder


def _init_memory(memory: Memory, backend: MemoryBackend, embedder: Embedder | None) -> None:
    backend.init_backend()
    memory._backend = backend
    memory._rag = RagIndex(backend, embedder if embedder is not None else HashEmbedder())
