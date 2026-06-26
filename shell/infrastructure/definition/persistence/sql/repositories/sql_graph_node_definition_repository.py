from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.repositories.graph_definition_repository.graph_node_definition_repository import (
    GraphNodeDefinitionRepository,
)
from shell.domain.definition.value_objects.ids import (  # noqa: TC002 — GraphNodeDefinitionId używany w konstruktorach w repozytorium
    GraphDefinitionId,
    GraphNodeDefinitionId,
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    graph_node_definition_entity_to_model,
    graph_node_definition_model_to_entity,
    graph_node_definition_update_model,
)
from sqlalchemy import select

from ..models import GraphDefinitionModel, GraphNodeDefinitionModel

if TYPE_CHECKING:
    from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphNodeDefinitionRepository(GraphNodeDefinitionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, graph_node_definition_execution_id: GraphNodeDefinitionId
    ) -> GraphNodeDefinition | None:
        graph_node_definition_query = select(GraphNodeDefinitionModel).where(
            GraphNodeDefinitionModel.id == graph_node_definition_execution_id.value
        )
        graph_node_definition = (
            await self._session.execute(graph_node_definition_query)
        ).scalar_one_or_none()
        return (
            graph_node_definition_model_to_entity(graph_node_definition)
            if graph_node_definition
            else None
        )

    async def save(
        self, graph_node_definition: GraphNodeDefinition, graph_definition_id: GraphDefinitionId
    ) -> None:
        graph_definition = await self._session.get(GraphDefinitionModel, graph_definition_id.value)
        if not graph_definition:
            raise ValueError(f"GraphDefinition {graph_definition_id.value} not found")

        model = await self._session.get(GraphNodeDefinitionModel, graph_node_definition.id.value)
        if model is None:
            model = graph_node_definition_entity_to_model(
                graph_node_definition, graph_definition_id.value
            )
            self._session.add(model)
        else:
            graph_node_definition_update_model(model, graph_node_definition)


__all__ = [
    "GraphNodeDefinitionModel",
    "SqlGraphNodeDefinitionRepository",
]
