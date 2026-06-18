from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.aggregates.graph_node_execution_input_payload import (
        GraphNodeExecutionInputPayload,
    )
    from shell.domain.value_objects.ids import GraphNodeExecutionId


class GraphNodeExecutionInputPayloadRepository(Protocol):
    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionInputPayload | None: ...

    async def save(self, payload: GraphNodeExecutionInputPayload) -> None: ...
