from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.definition.repositories.graph_definition_repository.graph_definition_repository import (
    GraphDefinitionRepository,
)
from shell.infrastructure.definition.graph_definition.persistence.sql.mappers import (
    graph_definition_entity_to_model,
    graph_definition_model_to_entity,
    graph_definition_update_model,
)

from ..models import GraphDefinitionModel

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )


class SqlGraphDefinitionRepository(GraphDefinitionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self) -> Select[tuple[GraphDefinitionModel]]:
        return select(GraphDefinitionModel)

    async def get_by_id(self, graph_definition_id: GraphDefinitionId) -> GraphDefinition | None:
        query = self._base_query().where(GraphDefinitionModel.id == graph_definition_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_definition_model_to_entity(row) if row else None

    async def save(self, graph_definition: GraphDefinition) -> None:
        model = await self._session.get(GraphDefinitionModel, graph_definition.id.value)
        if model is None:
            model = graph_definition_entity_to_model(graph_definition)
            self._session.add(model)
        else:
            graph_definition_update_model(model, graph_definition)

    async def list_all(self) -> list[GraphDefinition]:
        query = self._base_query()
        rows = (await self._session.execute(query)).scalars().all()
        return [graph_definition_model_to_entity(r) for r in rows if r is not None]


__all__ = [
    "GraphDefinitionModel",
    "SqlGraphDefinitionRepository",
]
