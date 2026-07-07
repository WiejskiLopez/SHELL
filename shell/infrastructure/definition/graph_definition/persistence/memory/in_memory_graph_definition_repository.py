from __future__ import annotations

from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.repositories import (
    GraphDefinitionRepository,
)
from shell.domain.definition.aggregates.graph_definition.value_objects import (
    GraphDefinitionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryGraphDefinitionRepository(
    InMemoryRepository[GraphDefinition, GraphDefinitionId], GraphDefinitionRepository
):
    async def get_by_id(self, id: GraphDefinitionId) -> GraphDefinition | None:
        return self._store.get(id.value)

    async def list_all(self) -> list[GraphDefinition]:
        return list(self._store.values())
