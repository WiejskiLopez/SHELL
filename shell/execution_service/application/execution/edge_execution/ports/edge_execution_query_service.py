from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution_service.application.execution.edge_execution.dto.edge_execution import (
        EdgeExecutionDto,
    )


class EdgeExecutionQueryService(Protocol):
    async def get_by_id(self, edge_execution_id: str) -> EdgeExecutionDto | None: ...
