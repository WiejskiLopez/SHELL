"""Unit tests for RagDocument entity."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from shell.domain.definition.aggregates.rag_document import RagChunk, RagDocument
from shell.domain.definition.value_objects.chunk_index import ChunkIndex
from shell.domain.definition.value_objects.chunk_text import ChunkText
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.definition.value_objects.domain_tag import DomainTag
from shell.domain.definition.value_objects.embedding import Embedding
from shell.domain.definition.value_objects.embedding_model import EmbeddingModel
from shell.domain.definition.value_objects.ids import RagChunkId, RagDocumentId
from shell.domain.definition.value_objects.source_uri import SourceUri
from shell.domain.definition.value_objects.title import Title

_NOW = datetime(2025, 1, 1, tzinfo=UTC)


class TestRagDocument:
    def _make_doc(self) -> RagDocument:
        return RagDocument.new(
            id_=RagDocumentId.generate(),
            source_uri=SourceUri("file:///a.md"),
            title=Title("Test Doc"),
            domain=DomainTag("test"),
            now=CreatedAt(_NOW),
        )

    def test_new_creates_document_with_no_chunks(self) -> None:
        doc = self._make_doc()
        assert list(doc.chunks) == []
        assert doc.source_uri == SourceUri("file:///a.md")
        assert doc.domain == DomainTag("test")

    def test_add_chunks_creates_correct_count(self) -> None:
        ids = [RagChunkId.generate() for _ in range(3)]
        texts = [ChunkText("chunk one"), ChunkText("chunk two"), ChunkText("chunk three")]
        embs = [Embedding(b"\x00" * 4), Embedding(b"\x00" * 4), Embedding(b"\x00" * 4)]
        doc = self._make_doc()
        doc.add_chunks(ids, texts, embs, EmbeddingModel("hash-stub"), now=CreatedAt(_NOW))
        assert len(doc.chunks) == 3
        assert doc.chunks[0].chunk_index == ChunkIndex(0)
        assert doc.chunks[2].chunk_text == ChunkText("chunk three")

    def test_add_chunks_mismatched_length_raises(self) -> None:
        doc = self._make_doc()
        with pytest.raises(ValueError, match="equal length"):
            doc.add_chunks(
                [RagChunkId.generate()],
                [ChunkText("a"), ChunkText("b")],
                [Embedding(b"\x00" * 4), Embedding(b"\x00" * 4)],
                EmbeddingModel("m"),
                now=CreatedAt(_NOW),
            )

    def test_empty_source_uri_raises(self) -> None:
        with pytest.raises(ValueError, match="SourceUri"):
            RagDocument.new(
                id_=RagDocumentId.generate(),
                source_uri=SourceUri(""),
                title=Title("T"),
                domain=DomainTag("d"),
                now=CreatedAt(_NOW),
            )

    def test_chunk_negative_index_raises(self) -> None:
        doc_id = RagDocumentId.generate()
        with pytest.raises(ValueError, match="ChunkIndex"):
            RagChunk(
                id=RagChunkId.generate(),
                document_id=doc_id,
                chunk_index=ChunkIndex(-1),
                chunk_text=ChunkText("x"),
                embedding=Embedding(b"\x00" * 4),
                embedding_model=EmbeddingModel("m"),
            )
