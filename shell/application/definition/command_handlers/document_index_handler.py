"""DocumentIndexHandler — chunk, embed, persist a RAG document."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.repositories.rag_repository import RagDocumentRepository
from shell.domain.definition.services.rag_index_service import Embedder, build_rag_document
from shell.domain.definition.value_objects.ids import RagChunkId, RagDocumentId

if TYPE_CHECKING:
    from shell.application.definition.commands.rag_commands import IndexDocumentCommand
    from shell.application.platform.ports.ports import Clock, IdGenerator, UnitOfWork


class DocumentIndexHandler:
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

    async def handle(self, command: IndexDocumentCommand) -> str:
        doc_id = self._id_generator.new_id(RagDocumentId)
        max_chunks = max(
            1,
            len(command.text)
            // max(1, command.chunk_size - command.overlap)
            + 2,
        )
        chunk_ids = [self._id_generator.new_id(RagChunkId) for _ in range(max_chunks)]
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
            await unit_of_work.repository(RagDocumentRepository).save(doc)
            unit_of_work.stage_events(doc.pull_events())
        return doc_id.value
