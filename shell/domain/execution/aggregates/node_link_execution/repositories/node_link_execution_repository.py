from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.aggregates.node_link_execution.node_link_execution import (
        NodeLinkExecution,
    )
    from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
        NodeLinkExecutionId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class NodeLinkExecutionRepository(Protocol):
    async def get_by_id(
        self,
        node_link_execution_id: NodeLinkExecutionId,
    ) -> NodeLinkExecution | None: ...

    async def list_by_graph_execution_id(
        self,
        graph_execution_id: GraphExecutionId,
    ) -> list[NodeLinkExecution]: ...

    async def list_by_node_execution_id(
        self,
        node_execution_id: NodeExecutionId,
    ) -> list[NodeLinkExecution]: ...

    async def save(self, link: NodeLinkExecution) -> None: ...

    async def delete(self, id: NodeLinkExecutionId) -> None: ...

    async def exists(self, id: NodeLinkExecutionId) -> ExistsResult: ...
