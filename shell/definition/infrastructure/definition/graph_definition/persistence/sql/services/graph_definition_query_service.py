from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.definition.application.definition.graph_definition.dto.graph_definition import (
    GraphDefinitionDto,
)
from shell.definition.application.definition.node_definition.dto.node_definition import (
    NodeDefinitionDto,
)
from shell.definition.infrastructure.definition.graph_definition.persistence.sql.models import (
    GraphDefinitionModel,
)
from shell.definition.infrastructure.definition.node_definition.persistence.sql.models import (
    NodeDefinitionModel,
)
from shell.definition.infrastructure.definition.node_link_definition.persistence.sql.models import (
    NodeLinkDefinitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.types import JsonStr


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

    async def get_graph_definition_by_semantic(
        self, semantic_query: JsonStr
    ) -> GraphDefinitionDto | None:
        try:
            payload = json.loads(semantic_query.value)
        except (TypeError, ValueError):
            return None

        default_id = payload.get("default_graph_definition_id")
        if not isinstance(default_id, str) or not default_id:
            return None
        return await self.get_by_id(default_id)

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
            created_at=model.created_at,
            node_definitions=[
                NodeDefinitionDto(
                    id=node.id,
                    node_type=node.node_type,
                    max_step=node.max_step,
                )
                for node in node_models
            ],
        )
