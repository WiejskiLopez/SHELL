from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.definition.graph_definition.dto.graph_definition import GraphDefinitionDto
from shell.application.definition.node_definition.dto.node_definition import NodeDefinitionDto
from shell.infrastructure.definition.graph_definition.persistence.sql.models import (
    GraphDefinitionModel,
)
from shell.infrastructure.definition.node_definition.persistence.sql.models import (
    NodeDefinitionModel,
)
from shell.infrastructure.definition.node_link_definition.persistence.sql.models import (
    NodeLinkDefinitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SqlGraphDefinitionQueryService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, definition_id: str) -> GraphDefinitionDto | None:
        async with self._session_factory() as session:
            stmt = select(GraphDefinitionModel).where(GraphDefinitionModel.id == definition_id)
            res = await session.execute(stmt)
            model = res.unique().scalar_one_or_none()
            if model is None:
                return None
            return await self._to_dto(session, model)

    async def _to_dto(
        self, session: AsyncSession, model: GraphDefinitionModel
    ) -> GraphDefinitionDto:
        link_stmt = (
            select(NodeDefinitionModel)
            .join(
                NodeLinkDefinitionModel,
                NodeLinkDefinitionModel.node_definition_id == NodeDefinitionModel.id,
            )
            .where(NodeLinkDefinitionModel.graph_definition_id == model.id)
        )
        node_models = (await session.execute(link_stmt)).scalars().all()

        return GraphDefinitionDto(
            id=model.id,
            node_definitions=[
                NodeDefinitionDto(
                    id=node.id,
                    node_type=node.node_type,
                    max_step=node.max_step,
                )
                for node in node_models
            ],
        )
