from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state_input.graph_execution_state_input import (
        GraphExecutionStateInput,
    )


class GraphExecutionStateInputRepository(Protocol):
    async def get_current_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> GraphExecutionStateInput | None: ...

    async def save(self, state: GraphExecutionStateInput) -> None: ...
