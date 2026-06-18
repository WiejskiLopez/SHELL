"""NodeResult aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.ids import GraphNodeExecutionId, GraphNodeExecutionResultId, WorkflowId
    from shell.domain.value_objects.status import Status


@dataclass(slots=True)
class GraphNodeExecutionResult:
    id: GraphNodeExecutionResultId
    graph_node_execution_id: GraphNodeExecutionId
    workflow_id: WorkflowId
    status: Status
    stdout: str
    stderr: str
    artifact_uri: str
    created_at: datetime

    @classmethod
    def new(
        cls,
        *,
        id_: GraphNodeExecutionResultId,
        graph_node_execution_id: GraphNodeExecutionId,
        workflow_id: WorkflowId,
        status: Status,
        stdout: str = "",
        stderr: str = "",
        artifact_uri: str = "",
        now: datetime,
    ) -> GraphNodeExecutionResult:
        return cls(
            id=id_,
            graph_node_execution_id=graph_node_execution_id,
            workflow_id=workflow_id,
            status=status,
            stdout=stdout,
            stderr=stderr,
            artifact_uri=artifact_uri,
            created_at=now,
        )
