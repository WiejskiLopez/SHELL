from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.repositories.graph_node_execution_input_payload_repository import (
    GraphNodeExecutionInputPayloadRepository,
)
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,  # noqa: TC002 — GraphNodeExecutionId używany w konstruktorach w repozytorium
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution_input_payload import (
        GraphNodeExecutionInputPayload,
    )


class InMemoryGraphNodeExecutionInputPayloadRepository(GraphNodeExecutionInputPayloadRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphNodeExecutionInputPayload] = {}

    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionInputPayload | None:
        for payload in self._store.values():
            if payload.graph_node_execution_id == graph_node_execution_id and payload.is_current:
                return payload
        return None

    async def save(self, payload: GraphNodeExecutionInputPayload) -> None:
        self._store[payload.id.value] = payload
