from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
        EdgeExecutionId,
    )
    from shell.domain.execution.aggregates.edge_link_execution.edge_link_execution import (
        EdgeLinkExecution,
    )
    from shell.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
        EdgeLinkExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class EdgeLinkExecutionRepository(Protocol):
    async def get_by_id(
        self,
        id_: EdgeLinkExecutionId,
    ) -> EdgeLinkExecution | None: ...

    async def save(self, link: EdgeLinkExecution) -> None: ...

    async def delete(self, id_: EdgeLinkExecutionId) -> None: ...

    async def exists(self, id_: EdgeLinkExecutionId) -> ExistsResult: ...

    async def list_by_node_execution_id(
        self,
        node_execution_id: NodeExecutionId,
    ) -> list[EdgeLinkExecution]: ...

    async def list_by_edge_execution_id(
        self,
        edge_execution_id: EdgeExecutionId,
    ) -> list[EdgeLinkExecution]: ...
