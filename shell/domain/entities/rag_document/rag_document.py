from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.entities.base.entity import Entity
from shell.domain.entities.rag_document.rag_chunk import RagChunk

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.ids import RagChunkId, RagDocumentId


class RagDocument(Entity[RagDocumentId]):
    __slots__ = ("source_uri", "title", "domain", "created_at", "chunks")

    def __init__(
        self,
        id: RagDocumentId,
        source_uri: str,
        title: str,
        domain: str,
        created_at: datetime,
        chunks: list[RagChunk] | None = None,
    ) -> None:
        if not source_uri:
            raise ValueError("source_uri cannot be empty")
        if not title:
            raise ValueError("title cannot be empty")
        if not domain:
            raise ValueError("domain cannot be empty")
        super().__init__(id)
        self.source_uri = source_uri
        self.title = title
        self.domain = domain
        self.created_at = created_at
        self.chunks = list(chunks) if chunks is not None else []

    @classmethod
    def new(
        cls,
        id_: RagDocumentId,
        source_uri: str,
        title: str,
        domain: str,
        now: datetime,
    ) -> RagDocument:
        return cls(
            id=id_,
            source_uri=source_uri,
            title=title,
            domain=domain,
            created_at=now,
        )

    def add_chunks(
        self,
        chunk_ids: list[RagChunkId],
        texts: list[str],
        embeddings: list[bytes],
        model: str,
    ) -> None:
        if not (len(chunk_ids) == len(texts) == len(embeddings)):
            raise ValueError("chunk_ids, texts and embeddings must have equal length")
        for i, (cid, text, emb) in enumerate(zip(chunk_ids, texts, embeddings, strict=False)):
            self.chunks.append(
                RagChunk(
                    id=cid,
                    document_id=self.id,
                    chunk_index=i,
                    chunk_text=text,
                    embedding=emb,
                    embedding_model=model,
                )
            )
