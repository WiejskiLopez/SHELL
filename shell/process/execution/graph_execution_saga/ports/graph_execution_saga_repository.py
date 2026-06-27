from __future__ import annotations

from typing import Protocol

from shell.process.execution.graph_execution_saga.state import (
    GraphExecutionSagaState,
)


class GraphExecutionSagaRepository(Protocol):
    async def save(self, saga: GraphExecutionSagaState) -> None: ...

    async def get_by_graph_execution_id(
        self, graph_execution_id: str,
    ) -> GraphExecutionSagaState | None: ...
