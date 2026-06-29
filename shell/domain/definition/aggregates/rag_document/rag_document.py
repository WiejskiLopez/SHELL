from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.definition.aggregates.rag_document.entities.rag_chunk import RagChunk
from shell.domain.definition.aggregates.rag_document.events.rag_document_chunks_added_event import (
    RagDocumentChunksAddedEvent,
)
from shell.domain.definition.value_objects.chunk_index import ChunkIndex
from shell.domain.definition.value_objects.chunk_text import ChunkText
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.definition.value_objects.domain_tag import DomainTag
from shell.domain.definition.value_objects.embedding import Embedding
from shell.domain.definition.value_objects.embedding_model import EmbeddingModel
from shell.domain.definition.value_objects.ids import RagDocumentId
from shell.domain.definition.value_objects.source_uri import SourceUri
from shell.domain.definition.value_objects.title import Title
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.definition.value_objects.ids import RagChunkId


class RagDocument(AggregateRoot[RagDocumentId]):
    __slots__ = ("_source_uri", "_title", "_domain", "_created_at", "_chunks")

    def __init__(
        self,
        id: RagDocumentId,
        source_uri: SourceUri,
        title: Title,
        domain: DomainTag,
        created_at: CreatedAt,
        chunks: list[RagChunk] | None = None,
    ) -> None:
        super().__init__(id)
        self._source_uri = source_uri if isinstance(source_uri, SourceUri) else SourceUri(source_uri)
        self._title = title if isinstance(title, Title) else Title(title)
        self._domain = domain if isinstance(domain, DomainTag) else DomainTag(domain)
        self._created_at = created_at if isinstance(created_at, CreatedAt) else CreatedAt(created_at)
        self._chunks = list(chunks) if chunks is not None else []

    @classmethod
    def restore(
        cls,
        id: RagDocumentId,
        source_uri: SourceUri,
        title: Title,
        domain: DomainTag,
        created_at: CreatedAt,
        chunks: list[RagChunk] | None = None,
    ) -> Self:
        return cls(
            id=id,
            source_uri=source_uri,
            title=title,
            domain=domain,
            created_at=created_at,
            chunks=chunks,
        )

    @property
    def source_uri(self) -> SourceUri:
        return self._source_uri

    @property
    def title(self) -> Title:
        return self._title

    @property
    def domain(self) -> DomainTag:
        return self._domain

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def chunks(self) -> tuple[RagChunk, ...]:
        return tuple(self._chunks)

    @classmethod
    def new(
        cls,
        id_: RagDocumentId,
        source_uri: SourceUri,
        title: Title,
        domain: DomainTag,
        now: CreatedAt,
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
        texts: list[ChunkText],
        embeddings: list[Embedding],
        model: EmbeddingModel,
        now: CreatedAt | None = None,
    ) -> None:
        if not (len(chunk_ids) == len(texts) == len(embeddings)):
            raise ValueError("chunk_ids, texts and embeddings must have equal length")
        for i, (cid, text, emb) in enumerate(zip(chunk_ids, texts, embeddings, strict=False)):
            self._chunks.append(
                RagChunk(
                    id=cid,
                    document_id=self.id,
                    chunk_index=ChunkIndex(i),
                    chunk_text=text,
                    embedding=emb,
                    embedding_model=model,
                )
            )
        self.append_event(
            RagDocumentChunksAddedEvent.now(self.id, chunk_count=ChunkIndex(len(chunk_ids)), model=model, now=(now or self._created_at))
        )
