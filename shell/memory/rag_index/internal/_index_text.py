from __future__ import annotations

from typing import TYPE_CHECKING

from shell.memory.rag_index.internal._chunk_text import _chunk_text
from shell.memory.rag_index.internal._encode_vector import _encode_vector

if TYPE_CHECKING:
    from shell.memory.rag_index.rag_index import RagIndex


def _index_text(
    rag: RagIndex,
    source_uri: str,
    title: str,
    domain: str,
    text: str,
    chunk_size: int,
    overlap: int,
) -> int:
    chunks = _chunk_text(text, chunk_size, overlap)
    if not chunks:
        return 0
    vectors = rag.embedder_.embed_batch(chunks)
    blobs = [_encode_vector(v) for v in vectors]
    rag.backend_.index_document(
        source_uri=source_uri,
        title=title,
        domain=domain,
        chunks=chunks,
        embeddings=blobs,
        embedding_model=rag.embedder_.model_name_,
    )
    return len(chunks)
