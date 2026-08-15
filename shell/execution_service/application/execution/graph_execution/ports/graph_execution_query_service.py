from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution_service.application.execution.graph_execution.dto.graph_execution import (
        GraphExecutionDto,
    )


class GraphExecutionQueryService(Protocol):
    async def get_by_id(self, graph_execution_id: str) -> GraphExecutionDto | None: ...
