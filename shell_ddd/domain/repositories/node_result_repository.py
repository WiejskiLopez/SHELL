from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.node_result import NodeResult
    from shell_ddd.domain.value_objects.ids import NodeId, NodeResultId, WorkflowId


class NodeResultRepository(Protocol):
    async def get_by_id(self, result_id: NodeResultId) -> NodeResult | None: ...
    async def get_by_node_and_workflow(self, node_id: NodeId, workflow_id: WorkflowId) -> NodeResult | None: ...
    async def save(self, result: NodeResult) -> None: ...
