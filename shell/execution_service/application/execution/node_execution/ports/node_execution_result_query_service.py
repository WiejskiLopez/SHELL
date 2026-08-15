from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution_service.application.execution.node_execution.dto.node_execution_result import (
        NodeExecutionResultDto,
    )


class NodeExecutionResultQueryService(Protocol):
    """Port do sprawdzania wyników wykonania konkretnych węzłów."""

    async def get_by_id(self, node_execution_id: str) -> NodeExecutionResultDto | None: ...

    async def get_node_execution_result(
        self, node_execution_id: str, workflow_id: str
    ) -> NodeExecutionResultDto | None: ...
