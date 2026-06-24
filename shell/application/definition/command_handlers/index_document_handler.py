"""IndexDocumentHandler — chunk, embed, persist a RAG document."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.services.rag_index_service import Embedder, build_rag_document

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import IndexDocumentCommand
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

    async def handle(self, command: IndexDocumentCommand) -> RagDocumentId:
        doc_id = self._id_generator.new_rag_document_id()
        # pre-generate enough chunk IDs (max chunks = ceil(len/step))
        max_chunks = max(1, len(command.text) // max(1, command.chunk_size - command.overlap) + 2)
        chunk_ids = [self._id_generator.new_rag_chunk_id() for _ in range(max_chunks)]
        doc = build_rag_document(
            doc_id=doc_id,
            chunk_ids=chunk_ids,
            source_uri=command.source_uri,
            title=command.title,
            domain=command.domain,
            text=command.text,
            embedder=self._embedder,
            now=self._clock.now(),
            chunk_size=command.chunk_size,
            overlap=command.overlap,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.rag_documents.save(doc)
        return doc_id
