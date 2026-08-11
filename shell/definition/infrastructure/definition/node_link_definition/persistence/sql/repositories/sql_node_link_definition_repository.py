from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.definition.domain.definition.aggregates.node_link_definition.repositories.node_link_definition_repository import (
    NodeLinkDefinitionRepository,
)
from shell.definition.infrastructure.definition.node_link_definition.persistence.sql.mappers import (
    node_link_definition_entity_to_model,
    node_link_definition_model_to_entity,
)
from shell.definition.infrastructure.definition.node_link_definition.persistence.sql.models import (
    NodeLinkDefinitionModel,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.definition.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.definition.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
        NodeDefinitionId,
    )
    from shell.definition.domain.definition.aggregates.node_link_definition.node_link_definition import (
        NodeLinkDefinition,
    )
    from shell.definition.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
        NodeLinkDefinitionId,
    )


class SqlNodeLinkDefinitionRepository(NodeLinkDefinitionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        node_link_definition_id: NodeLinkDefinitionId,
    ) -> NodeLinkDefinition | None:
        model = await self._session.get(NodeLinkDefinitionModel, node_link_definition_id.value)
        if model is None:
            return None
        return node_link_definition_model_to_entity(model)

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[NodeLinkDefinition]:
        stmt = select(NodeLinkDefinitionModel).where(
            NodeLinkDefinitionModel.graph_definition_id == graph_definition_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [node_link_definition_model_to_entity(m) for m in models]

    async def list_by_node_definition_id(
        self,
        node_definition_id: NodeDefinitionId,
    ) -> list[NodeLinkDefinition]:
        stmt = select(NodeLinkDefinitionModel).where(
            NodeLinkDefinitionModel.node_definition_id == node_definition_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [node_link_definition_model_to_entity(m) for m in models]

    async def save(self, link: NodeLinkDefinition) -> None:
        model = await self._session.get(
            NodeLinkDefinitionModel,
            link.id.value,
        )
        if model is None:
            model = node_link_definition_entity_to_model(link)
            self._session.add(model)

    async def delete(self, id: NodeLinkDefinitionId, now: datetime | None = None) -> None:
        model = await self._session.get(NodeLinkDefinitionModel, id.value)
        if model is not None:
            model.deleted_at = now

    async def exists(self, id: NodeLinkDefinitionId) -> ExistsResult:
        model = await self._session.get(NodeLinkDefinitionModel, id.value)
        return ExistsResult(model is not None)
