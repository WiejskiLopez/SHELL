from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution_service.application.execution.graph_execution.dto.graph_execution import (
    GraphExecutionDto,
)
from shell.execution_service.infrastructure.execution.graph_execution.persistence.sql.models.graph_execution import (
    GraphExecutionModel,
)
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class GraphExecutionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, graph_execution_id: str) -> GraphExecutionDto | None:
        async with self._session_factory() as session:
            stmt = select(GraphExecutionModel).where(GraphExecutionModel.id == graph_execution_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return GraphExecutionDto(
                id=model.id,
                graph_definition_id=model.graph_definition_id,
                task_execution_id=model.task_execution_id,
                parent_graph_execution_id=model.parent_graph_execution_id,
                state_data=JsonStr(
                    json.dumps({"input": model.state_input, "output": model.state_output})
                ),
                depth=model.depth,
                timeout_at=model.timeout_at,
            )
