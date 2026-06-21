"""Unit tests for RagDocument entity."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from shell.domain.definition.entities.rag_document import RagChunk, RagDocument
from shell.domain.definition.value_objects.ids import RagChunkId, RagDocumentId

_NOW = datetime(2025, 1, 1, tzinfo=UTC)


class TestRagDocument:
    def _make_doc(self) -> RagDocument:
        return RagDocument.new(
            id_=RagDocumentId.generate(),
            source_uri="file:///a.md",
            title="Test Doc",
            domain="test",
            now=_NOW,
        )

    def test_new_creates_document_with_no_chunks(self) -> None:
        doc = self._make_doc()
        assert doc.chunks == []
        assert doc.source_uri == "file:///a.md"
        assert doc.domain == "test"

    def test_add_chunks_creates_correct_count(self) -> None:
        ids = [RagChunkId.generate() for _ in range(3)]
        texts = ["chunk one", "chunk two", "chunk three"]
        embs = [b"\x00" * 4, b"\x00" * 4, b"\x00" * 4]
        doc = self._make_doc()
        doc.add_chunks(ids, texts, embs, "hash-stub")
        assert len(doc.chunks) == 3
        assert doc.chunks[0].chunk_index == 0
        assert doc.chunks[2].chunk_text == "chunk three"

    def test_add_chunks_mismatched_length_raises(self) -> None:
        doc = self._make_doc()
        with pytest.raises(ValueError, match="equal length"):
            doc.add_chunks([RagChunkId.generate()], ["a", "b"], [b"\x00" * 4, b"\x00" * 4], "m")

    def test_empty_source_uri_raises(self) -> None:
        with pytest.raises(ValueError, match="source_uri"):
            RagDocument.new(
                id_=RagDocumentId.generate(), source_uri="", title="T", domain="d", now=_NOW
            )

    def test_chunk_negative_index_raises(self) -> None:
        doc_id = RagDocumentId.generate()
        with pytest.raises(ValueError, match="chunk_index"):
            RagChunk(
                id=RagChunkId.generate(),
                document_id=doc_id,
                chunk_index=-1,
                chunk_text="x",
                embedding=b"\x00" * 4,
                embedding_model="m",
            )
