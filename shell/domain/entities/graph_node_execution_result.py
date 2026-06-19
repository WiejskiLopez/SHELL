"""NodeResult aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.entities.base.entity import Entity

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.ids import (
        GraphNodeExecutionId,
        GraphNodeExecutionResultId,
        WorkflowId,
    )
    from shell.domain.value_objects.status import Status


class GraphNodeExecutionResult(Entity[GraphNodeExecutionResultId]):
    __slots__ = (
        "graph_node_execution_id",
        "workflow_id",
        "status",
        "stdout",
        "stderr",
        "artifact_uri",
        "created_at",
    )

    def __init__(
        self,
        id: GraphNodeExecutionResultId,
        graph_node_execution_id: GraphNodeExecutionId,
        workflow_id: WorkflowId,
        status: Status,
        stdout: str,
        stderr: str,
        artifact_uri: str,
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self.graph_node_execution_id = graph_node_execution_id
        self.workflow_id = workflow_id
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.artifact_uri = artifact_uri
        self.created_at = created_at

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
