from __future__ import annotations

from shell.definition_service.domain.definition.aggregates.graph_definition.graph_definition import (
    GraphDefinition,
)
from shell.definition_service.domain.definition.aggregates.graph_definition.repositories import (
    GraphDefinitionRepository,
)
from shell.definition_service.domain.definition.aggregates.graph_definition.value_objects import (
    GraphDefinitionId,
)
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository


class InMemoryGraphDefinitionRepository(
    InMemoryRepository[GraphDefinition, GraphDefinitionId], GraphDefinitionRepository
):
    async def get_by_id(self, id: GraphDefinitionId) -> GraphDefinition | None:
        return self._store.get(id.value)

    async def list_all(self) -> list[GraphDefinition]:
        return list(self._store.values())
