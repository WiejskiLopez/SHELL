from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution_service.application.execution.node_execution.dto.node_execution import (
        NodeExecutionDto,
    )


class NodeExecutionQueryService(Protocol):
    """Port do odczytu agregatu NodeExecution (read model)."""

    async def get_by_id(self, node_execution_id: str) -> NodeExecutionDto | None: ...