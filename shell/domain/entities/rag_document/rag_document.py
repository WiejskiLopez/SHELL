from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shell.domain.entities.rag_document.rag_chunk import RagChunk

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.ids import RagChunkId, RagDocumentId


@dataclass(slots=True)
class RagDocument:
    id: RagDocumentId
    source_uri: str
    title: str
    domain: str
    created_at: datetime
    chunks: list[RagChunk] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.source_uri:
            raise ValueError("source_uri cannot be empty")
        if not self.title:
            raise ValueError("title cannot be empty")
        if not self.domain:
            raise ValueError("domain cannot be empty")

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
