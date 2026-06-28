"""IndexDocumentHandler — chunk, embed, persist a RAG document."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.services.rag_index_service import Embedder, build_rag_document

if TYPE_CHECKING:
    from shell.application.platform.commands import IndexDocumentCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork
    from shell.domain.definition.value_objects.ids import RagDocumentId


class IndexDocumentHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        embedder: Embedder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._embedder = embedder

    async def handle(self, index_document_command: IndexDocumentCommand) -> RagDocumentId:
        doc_id = self._id_generator.new_rag_document_id()
        max_chunks = max(1, len(index_document_command.text) // max(1, index_document_command.chunk_size - index_document_command.overlap) + 2)
        chunk_ids = [self._id_generator.new_rag_chunk_id() for _ in range(max_chunks)]
        doc = build_rag_document(
            doc_id=doc_id,
            chunk_ids=chunk_ids,
            source_uri=index_document_command.source_uri,
            title=index_document_command.title,
            domain=index_document_command.domain,
            text=index_document_command.text,
            embedder=self._embedder,
            now=self._clock.now(),
            chunk_size=index_document_command.chunk_size,
            overlap=index_document_command.overlap,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.rag_document_repository.save(doc)
        return doc_id
