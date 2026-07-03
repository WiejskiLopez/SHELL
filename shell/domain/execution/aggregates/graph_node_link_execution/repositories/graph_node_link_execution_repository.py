from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_link_execution.graph_node_link_execution import (
        GraphNodeLinkExecution,
    )
    from shell.domain.execution.aggregates.graph_node_link_execution.value_objects.graph_node_link_execution_id import (
        GraphNodeLinkExecutionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


class GraphNodeLinkExecutionRepository(Protocol):
    async def get_by_id(
        self,
        graph_node_link_execution_id: GraphNodeLinkExecutionId,
    ) -> GraphNodeLinkExecution | None: ...

    async def list_by_graph_execution_id(
        self,
        graph_execution_id: GraphExecutionId,
    ) -> list[GraphNodeLinkExecution]: ...

    async def list_by_graph_node_execution_id(
        self,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> list[GraphNodeLinkExecution]: ...

    async def save(self, link: GraphNodeLinkExecution) -> None: ...

    async def delete(self, id: GraphNodeLinkExecutionId) -> None: ...

    async def exists(self, id: GraphNodeLinkExecutionId) -> ExistsResult: ...
