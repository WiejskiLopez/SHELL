from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.repositories.graph_node_execution_output_payload_repository import (
    GraphNodeExecutionOutputPayloadRepository,
)
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution_output_payload import (
        GraphNodeExecutionOutputPayload,
    )


class InMemoryGraphNodeExecutionOutputPayloadRepository(GraphNodeExecutionOutputPayloadRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphNodeExecutionOutputPayload] = {}

    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionOutputPayload | None:
        for payload in self._store.values():
            if payload.graph_node_execution_id == graph_node_execution_id and payload.is_current:
                return payload
        return None

    async def save(self, payload: GraphNodeExecutionOutputPayload) -> None:
        self._store[payload.id.value] = payload
