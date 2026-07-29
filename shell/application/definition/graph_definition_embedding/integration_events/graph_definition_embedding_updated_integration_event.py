from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class GraphDefinitionEmbeddingUpdatedIntegrationEvent(IntegrationEvent):
    graph_definition_embedding_id: str
