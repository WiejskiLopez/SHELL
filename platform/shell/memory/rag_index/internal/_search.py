from __future__ import annotations

from typing import TYPE_CHECKING

from shell.memory.rag_index.internal._encode_vector import _encode_vector

if TYPE_CHECKING:
    from shell.memory.rag_index.rag_index import RagIndex


def _search(rag: RagIndex, query: str, top_k: int, domain: str | None) -> list[dict]:
    query_vector = rag.embedder_.embed_text(query)
    query_blob = _encode_vector(query_vector)
    return rag.backend_.search_rag(query_blob, top_k=top_k, domain=domain)
