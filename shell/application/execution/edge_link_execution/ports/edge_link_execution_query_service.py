from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.execution.edge_link_execution.dto.edge_link_execution import (
        EdgeLinkExecutionDto,
    )


class EdgeLinkExecutionQueryService(Protocol):
    async def get_by_id(self, edge_link_execution_id: str) -> EdgeLinkExecutionDto | None: ...
