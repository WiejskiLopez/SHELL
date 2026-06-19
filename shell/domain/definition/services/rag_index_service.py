"""RagIndexService — domain service: chunk text, embed, attach to RagDocument."""

from __future__ import annotations

import math
import struct
from typing import TYPE_CHECKING, Protocol

from shell.domain.definition.entities.rag_document import RagDocument

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.platform.value_objects.ids import RagChunkId, RagDocumentId


class Embedder(Protocol):
    """Port — embed text into a float vector."""

    @property
    def model_name(self) -> str: ...

    @property
    def dim(self) -> int: ...

    def embed_text(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


def _encode_vector(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    step = chunk_size - overlap
    for start in range(0, len(text), step):
        chunk = text[start : start + chunk_size]
        if not chunk:
            break
        chunks.append(chunk)
        if start + chunk_size >= len(text):
            break
    return chunks


def build_rag_document(
    doc_id: RagDocumentId,
    chunk_ids: list[RagChunkId],
    source_uri: str,
    title: str,
    domain: str,
    text: str,
    embedder: Embedder,
    now: datetime,
    chunk_size: int = 500,
    overlap: int = 50,
) -> RagDocument:
    """Chunk *text*, embed each chunk, return a fully-built RagDocument aggregate."""
    doc = RagDocument.new(
        id_=doc_id,
        source_uri=source_uri,
        title=title,
        domain=domain,
        now=now,
    )
    chunks = chunk_text(text, chunk_size, overlap)
    if not chunks:
        return doc
    if len(chunk_ids) < len(chunks):
        raise ValueError(f"Not enough chunk_ids supplied: need {len(chunks)}, got {len(chunk_ids)}")
    vectors = embedder.embed_batch(chunks)
    blobs = [_encode_vector(vector) for vector in vectors]
    doc.add_chunks(
        chunk_ids=chunk_ids[: len(chunks)],
        texts=chunks,
        embeddings=blobs,
        model=embedder.model_name,
    )
    return doc


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if len(vector_a) != len(vector_b) or not vector_a:
        return 0.0
    dot = sum(component_a * component_b for component_a, component_b in zip(vector_a, vector_b, strict=False))
    norm_a = math.sqrt(sum(component * component for component in vector_a))
    norm_b = math.sqrt(sum(component * component for component in vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
