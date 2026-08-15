from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.definition_service.application.definition.node_definition.dto.node_definition import (
    NodeDefinitionDto,
)
from shell.definition_service.infrastructure.definition.node_definition.persistence.sql.models.node_definition import (
    NodeDefinitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class NodeDefinitionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, node_definition_id: str) -> NodeDefinitionDto | None:
        async with self._session_factory() as session:
            stmt = select(NodeDefinitionModel).where(NodeDefinitionModel.id == node_definition_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return NodeDefinitionDto(
                id=model.id,
                node_type=model.node_type,
                max_step=model.max_step,
            )
