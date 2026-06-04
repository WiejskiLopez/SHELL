from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _search_fts(backend: SqlMemoryBackend, query_text: str, top_k: int) -> list[dict]:
    if not backend.driver_.dialect_.supports_fts_:
        return []
    rows = backend.driver_.query(
        """
        SELECT c.id, c.document_id, c.chunk_index, c.chunk_text,
               d.source_uri, d.title, d.domain,
               bm25(rag_chunk_fts) AS score
        FROM rag_chunk_fts
        JOIN rag_chunk c ON c.id = rag_chunk_fts.rowid
        JOIN rag_document d ON d.id = c.document_id
        WHERE rag_chunk_fts MATCH ?
        ORDER BY score
        LIMIT ?
        """,
        (query_text, top_k),
    )
    return [
        {
            "score": r["score"],
            "chunk_id": r["id"],
            "document_id": r["document_id"],
            "chunk_index": r["chunk_index"],
            "chunk_text": r["chunk_text"],
            "source_uri": r["source_uri"],
            "title": r["title"],
            "domain": r["domain"],
        }
        for r in rows
    ]
