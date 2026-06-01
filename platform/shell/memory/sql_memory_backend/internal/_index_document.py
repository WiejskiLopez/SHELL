from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _index_document(
    backend: SqlMemoryBackend,
    source_uri: str,
    title: str,
    domain: str,
    chunks: list[str],
    embeddings: list[bytes],
    embedding_model: str,
) -> int:
    if len(chunks) != len(embeddings):
        raise ValueError("[SqlMemoryBackend.index_document] chunks and embeddings length mismatch")
    now = datetime.now(timezone.utc).isoformat()
    backend.driver_.execute(
        "INSERT INTO rag_document (source_uri, title, domain, created_at) VALUES (?, ?, ?, ?)",
        (source_uri, title, domain, now),
    )
    document_id = backend.driver_.last_insert_id()
    backend.driver_.executemany(
        """
        INSERT INTO rag_chunk (document_id, chunk_index, chunk_text, embedding, embedding_model)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (document_id, idx, chunk, emb, embedding_model)
            for idx, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ],
    )
    if backend.driver_.dialect_.supports_fts_:
        backend.driver_.executemany(
            "INSERT INTO rag_chunk_fts(rowid, chunk_text) "
            "SELECT id, chunk_text FROM rag_chunk WHERE document_id = ? AND chunk_index = ?",
            [(document_id, idx) for idx in range(len(chunks))],
        )
    backend.driver_.commit()
    return document_id
