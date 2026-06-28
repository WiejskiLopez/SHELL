from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition.events.graph_definition_created_event import (
    GraphDefinitionCreatedEvent,
)
from shell.domain.definition.aggregates.graph_definition_embedding.graph_definition_embedding import (
    GraphDefinitionEmbedding,
)
from shell.domain.definition.value_objects.embedding import Embedding
from shell.domain.definition.value_objects.embedding_model import EmbeddingModel
from shell.domain.definition.value_objects.embedding_text import EmbeddingText

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.platform.ports.time import Clock
    from shell.domain.definition.services.rag_index_service import Embedder


class GenerateEmbeddingOnGraphDefinitionCreatedHandler:
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

    async def handle(self, event: GraphDefinitionCreatedEvent) -> None:
        text = f"{event.name.value} {event.purpose.value}"
        vector = self._embedder.embed_text(text)
        vector_bytes = struct.pack(f"{len(vector)}f", *vector)

        embedding_id = self._id_generator.new_graph_definition_embedding_id()

        async with self._unit_of_work as unit_of_work:
            if await unit_of_work.graph_definition_embedding_repository.get_by_graph_definition_id(
                event.graph_definition_id,
            ) is not None:
                return

            embedding_aggregate = GraphDefinitionEmbedding.create(
                id=embedding_id,
                graph_definition_id=event.graph_definition_id,
                text=EmbeddingText(text),
                embedding=Embedding(vector_bytes),
                model=EmbeddingModel(self._embedder.model_name),
                now=self._clock.now(),
            )
            await unit_of_work.graph_definition_embedding_repository.save(embedding_aggregate)
            unit_of_work.stage_events(embedding_aggregate.pull_events())
