from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from shell.application.definition.dto.graph_definition import GraphDefinitionDto
from shell.application.definition.dto.graph_node_definition import GraphNodeDefinitionDto
from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel,
    GraphNodeDefinitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SqlGraphDefinitionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_graph_definition_by_name(self, name: str) -> GraphDefinitionDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(GraphDefinitionModel)
                .options(joinedload(GraphDefinitionModel.graph_node_execution_models))
                .where(GraphDefinitionModel.name == name)
            )
            res = await session.execute(stmt)
            model = res.unique().scalar_one_or_none()
            if model is None:
                return None
            return self._to_dto(model)

    async def get_graph_definition(self, definition_id: str) -> GraphDefinitionDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(GraphDefinitionModel)
                .options(joinedload(GraphDefinitionModel.graph_node_execution_models))
                .where(GraphDefinitionModel.id == definition_id)
            )
            res = await session.execute(stmt)
            model = res.unique().scalar_one_or_none()
            if model is None:
                return None
            return self._to_dto(model)

    def _to_dto(self, model: GraphDefinitionModel) -> GraphDefinitionDto:
        return GraphDefinitionDto(
            id=model.id,
            name=model.name,
            purpose=model.purpose,
            graph_node_definitions=[
                GraphNodeDefinitionDto(
                    id=nd.id,
                    position=nd.position,
                    mode=nd.mode,
                    role=nd.role,
                    node_type=nd.node_type,
                    model=nd.model,
                    command=nd.command,
                    timeout=nd.timeout,
                    retries=nd.retries,
                    log_level=nd.log_level,
                    max_step=nd.max_step,
                    no_ask_user=nd.no_ask_user,
                    autopilot=nd.autopilot,
                    status_initial=nd.status_initial,
                    extra=nd.extra or {},
                    script=nd.script or "",
                    script_type=nd.script_type or "",
                )
                for nd in model.graph_node_execution_models or []
            ],
        )
