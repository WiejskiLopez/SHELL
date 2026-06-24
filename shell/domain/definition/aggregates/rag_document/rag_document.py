from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.rag_document.entities.rag_chunk import RagChunk
from shell.domain.definition.value_objects.ids import RagDocumentId
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.definition.value_objects.ids import RagChunkId


class RagDocument(AggregateRoot[RagDocumentId]):
    __slots__ = ("_source_uri", "_title", "_domain", "_created_at", "_chunks")

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
        self._source_uri = source_uri
        self._title = title
        self._domain = domain
        self._created_at = created_at
        self._chunks = list(chunks) if chunks is not None else []

    @property
    def source_uri(self) -> str:
        return self._source_uri

    @property
    def title(self) -> str:
        return self._title

    @property
    def domain(self) -> str:
        return self._domain

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def chunks(self) -> tuple[RagChunk, ...]:
        return tuple(self._chunks)

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
            self._chunks.append(
                RagChunk(
                    id=cid,
                    document_id=self.id,
                    chunk_index=i,
                    chunk_text=text,
                    embedding=emb,
                    embedding_model=model,
                )
            )
