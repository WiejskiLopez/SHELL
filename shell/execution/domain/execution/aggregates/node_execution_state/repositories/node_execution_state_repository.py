from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.execution.domain.execution.aggregates.node_execution_state.node_execution_state import (
        NodeExecutionState,
    )
    from shell.execution.domain.execution.aggregates.node_execution_state.value_objects.node_execution_state_id import (
        NodeExecutionStateId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult
    from shell.platform.domain.value_objects.state_direction import StateDirection


class NodeExecutionStateRepository(Protocol):
    async def get_by_id(self, id_: NodeExecutionStateId) -> NodeExecutionState | None: ...

    async def list_by_node_execution_id(
        self, node_execution_id: NodeExecutionId
    ) -> list[NodeExecutionState]: ...

    async def list_by_node_execution_and_direction(
        self, node_execution_id: NodeExecutionId, direction: StateDirection
    ) -> list[NodeExecutionState]: ...

    async def save(self, state: NodeExecutionState) -> None: ...

    async def delete(self, id_: NodeExecutionStateId) -> None: ...

    async def exists(self, id_: NodeExecutionStateId) -> ExistsResult: ...
