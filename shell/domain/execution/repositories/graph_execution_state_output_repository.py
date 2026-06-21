from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.graph_execution_state_output import (
        GraphExecutionStateOutput,
    )
    from shell.domain.execution.value_objects.ids import GraphExecutionId


class GraphExecutionStateOutputRepository(Protocol):
    async def get_current_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> GraphExecutionStateOutput | None: ...

    async def save(self, state: GraphExecutionStateOutput) -> None: ...
