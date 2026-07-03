from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.definition.aggregates.graph_node_link_definition.value_objects.graph_node_link_definition_id import (
    GraphNodeLinkDefinitionId,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.definition.persistence.sql.models import (
    GraphNodeLinkDefinitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_link_definition.graph_node_link_definition import (
        GraphNodeLinkDefinition,
    )


class SqlGraphNodeLinkDefinitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        graph_node_link_definition_id: GraphNodeLinkDefinitionId,
    ) -> GraphNodeLinkDefinition | None:
        model = await self._session.get(
            GraphNodeLinkDefinitionModel, graph_node_link_definition_id.value
        )
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[GraphNodeLinkDefinition]:
        stmt = select(GraphNodeLinkDefinitionModel).where(
            GraphNodeLinkDefinitionModel.graph_definition_id == graph_definition_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def list_by_graph_node_definition_id(
        self,
        graph_node_definition_id: GraphNodeDefinitionId,
    ) -> list[GraphNodeLinkDefinition]:
        stmt = select(GraphNodeLinkDefinitionModel).where(
            GraphNodeLinkDefinitionModel.graph_node_definition_id
            == graph_node_definition_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def save(self, link: GraphNodeLinkDefinition) -> None:
        model = await self._session.get(
            GraphNodeLinkDefinitionModel,
            link.id.value,
        )
        if model is None:
            model = self._entity_to_model(link)
            self._session.add(model)

    async def delete(self, id: GraphNodeLinkDefinitionId) -> None:
        model = await self._session.get(GraphNodeLinkDefinitionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: GraphNodeLinkDefinitionId) -> ExistsResult:
        model = await self._session.get(GraphNodeLinkDefinitionModel, id.value)
        return ExistsResult(model is not None)

    def _model_to_entity(
        self,
        model: GraphNodeLinkDefinitionModel,
    ) -> GraphNodeLinkDefinition:
        return GraphNodeLinkDefinition(
            id=GraphNodeLinkDefinitionId(model.id),
            graph_definition_id=GraphDefinitionId(model.graph_definition_id),
            graph_node_definition_id=GraphNodeDefinitionId(model.graph_node_definition_id),
        )

    def _entity_to_model(
        self,
        entity: GraphNodeLinkDefinition,
    ) -> GraphNodeLinkDefinitionModel:
        return GraphNodeLinkDefinitionModel(
            id=entity.id.value,
            graph_definition_id=entity.graph_definition_id.value,
            graph_node_definition_id=entity.graph_node_definition_id.value,
        )
