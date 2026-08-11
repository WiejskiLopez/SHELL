from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.edge_execution.edge_execution import (
        EdgeExecution,
    )
    from shell.execution.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
        EdgeExecutionId,
    )
    from shell.execution.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class EdgeExecutionRepository(Protocol):
    async def get_by_id(self, id_: EdgeExecutionId) -> EdgeExecution | None: ...

    async def save(self, edge: EdgeExecution) -> None: ...

    async def delete(self, id_: EdgeExecutionId) -> None: ...

    async def exists(self, id_: EdgeExecutionId) -> ExistsResult: ...

    async def list_by_source_node(self, node_id: NodeExecutionId) -> list[EdgeExecution]: ...

    async def list_by_target_node(self, node_id: NodeExecutionId) -> list[EdgeExecution]: ...
