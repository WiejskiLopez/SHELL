from __future__ import annotations

from typing import Protocol

from shell.application.platform.dto import (
    GraphNodeExecutionResultDto,  # noqa: TC002 — GraphNodeExecutionResultDto używany jako typ zwracany w sygnaturze Protocol
)


class GraphNodeExecutionResultQueryService(Protocol):
    """Port do sprawdzania wyników wykonania konkretnych węzłów."""

    async def get_graph_node_execution_result(
        self, graph_node_execution_id: str, workflow_id: str
    ) -> GraphNodeExecutionResultDto | None: ...
