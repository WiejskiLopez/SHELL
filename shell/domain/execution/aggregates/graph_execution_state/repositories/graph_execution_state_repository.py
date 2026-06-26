from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )
    from shell.domain.execution.value_objects.state_kind import StateKind
    from shell.domain.execution.value_objects.exists_result import ExistsResult


class GraphExecutionStateRepository(Protocol):
    async def get_current_by_graph_execution_id_and_kind(
        self, graph_execution_id: GraphExecutionId, kind: StateKind
    ) -> GraphExecutionState | None: ...

    async def save(self, state: GraphExecutionState) -> None: ...
    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> ExistsResult: ...
