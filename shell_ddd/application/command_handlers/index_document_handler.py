"""IndexDocumentHandler — chunk, embed, persist a RAG document."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.services.rag_index_service import Embedder, build_rag_document

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import IndexDocumentCommand
    from shell_ddd.application.ports.ports import Clock, IdGenerator, UnitOfWork
    from shell_ddd.domain.value_objects.ids import RagDocumentId


class IndexDocumentHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        embedder: Embedder,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._embedder = embedder

    async def handle(self, cmd: IndexDocumentCommand) -> RagDocumentId:
        doc_id = self._id_gen.new_rag_document_id()
        # pre-generate enough chunk IDs (max chunks = ceil(len/step))
        max_chunks = max(1, len(cmd.text) // max(1, cmd.chunk_size - cmd.overlap) + 2)
        chunk_ids = [self._id_gen.new_rag_chunk_id() for _ in range(max_chunks)]
        doc = build_rag_document(
            doc_id=doc_id,
            chunk_ids=chunk_ids,
            source_uri=cmd.source_uri,
            title=cmd.title,
            domain=cmd.domain,
            text=cmd.text,
            embedder=self._embedder,
            now=self._clock.now(),
            chunk_size=cmd.chunk_size,
            overlap=cmd.overlap,
        )
        async with self._uow as uow:
            await uow.rag_documents.save(doc)
            await uow.commit()
        return doc_id
