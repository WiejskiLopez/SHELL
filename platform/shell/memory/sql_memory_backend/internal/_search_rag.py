from __future__ import annotations

import struct
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _decode_vector(blob: bytes) -> list[float]:
    count = len(blob) // 4
    return list(struct.unpack(f"{count}f", blob))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _search_rag(
    backend: SqlMemoryBackend,
    query_embedding: bytes,
    top_k: int,
    domain: str | None,
) -> list[dict]:
    query_vec = _decode_vector(query_embedding)
    if domain:
        rows = backend.driver_.query(
            """
            SELECT c.id, c.document_id, c.chunk_index, c.chunk_text, c.embedding,
                   d.source_uri, d.title, d.domain
            FROM rag_chunk c JOIN rag_document d ON d.id = c.document_id
            WHERE d.domain = ? AND c.embedding IS NOT NULL
            """,
            (domain,),
        )
    else:
        rows = backend.driver_.query(
            """
            SELECT c.id, c.document_id, c.chunk_index, c.chunk_text, c.embedding,
                   d.source_uri, d.title, d.domain
            FROM rag_chunk c JOIN rag_document d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
            """,
        )
    scored = []
    for r in rows:
        score = _cosine_similarity(query_vec, _decode_vector(r["embedding"]))
        scored.append((score, r))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [
        {
            "score": score,
            "chunk_id": r["id"],
            "document_id": r["document_id"],
            "chunk_index": r["chunk_index"],
            "chunk_text": r["chunk_text"],
            "source_uri": r["source_uri"],
            "title": r["title"],
            "domain": r["domain"],
        }
        for score, r in scored[:top_k]
    ]
