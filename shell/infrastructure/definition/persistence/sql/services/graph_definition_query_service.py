from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.dto.graph_definition import GraphDefinitionDto
from shell.application.definition.dto.graph_node_definition import GraphNodeDefinitionDto
from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel,
)
from sqlalchemy import select
from sqlalchemy.orm import joinedload

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
                    id=graph_node_definition.id,
                    position=graph_node_definition.position,
                    mode=graph_node_definition.mode,
                    role=graph_node_definition.role,
                    node_type=graph_node_definition.node_type,
                    model=graph_node_definition.model or "",
                    command=graph_node_definition.command,
                    timeout=graph_node_definition.timeout,
                    retries=graph_node_definition.retries,
                    log_level=graph_node_definition.log_level,
                    max_step=graph_node_definition.max_step,
                    no_ask_user=graph_node_definition.no_ask_user or False,
                    autopilot=graph_node_definition.autopilot or False,
                    status_initial=graph_node_definition.status_initial,
                    script=graph_node_definition.script or "",
                    script_type=graph_node_definition.script_type or "",
                )
                for graph_node_definition in model.graph_node_execution_models or []
            ],
        )
