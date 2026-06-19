from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shell.domain.repositories.graph_definition_repository.graph_definition_repository import GraphDefinitionRepository
from shell.domain.value_objects.ids import GraphDefinitionId

from ..mappers import (
    graph_definition_entity_to_model,
    graph_definition_model_to_entity,
)
from ..models import GraphDefinitionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.entities.graph_definition import GraphDefinition


class SqlGraphDefinitionRepository(GraphDefinitionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, graph_definition_id: GraphDefinitionId) -> GraphDefinition | None:
        query = select(GraphDefinitionModel).where(GraphDefinitionModel.id == graph_definition_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_definition_model_to_entity(row) if row else None

    async def get_graph_definition_by_name(
        self, graph_definition_by_name: str
    ) -> GraphDefinition | None:
        query = (
            select(GraphDefinitionModel)
            .options(selectinload(GraphDefinitionModel.graph_node_execution_models))
            .where(GraphDefinitionModel.name == graph_definition_by_name)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_definition_model_to_entity(row) if row else None

    async def save(self, graph_definition: GraphDefinition) -> None:
        graph_definition_model = graph_definition_entity_to_model(graph_definition)
        await self._session.merge(graph_definition_model)
