from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.aggregates.graph_node_execution_output_payload import (
        GraphNodeExecutionOutputPayload,
    )
    from shell.domain.value_objects.ids import GraphNodeExecutionId


class GraphNodeExecutionOutputPayloadRepository(Protocol):
    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionOutputPayload | None: ...

    async def save(self, payload: GraphNodeExecutionOutputPayload) -> None: ...
