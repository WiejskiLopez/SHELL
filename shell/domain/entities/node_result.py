"""NodeResult aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.ids import NodeId, NodeResultId, WorkflowId
    from shell.domain.value_objects.status import Status


@dataclass(slots=True)
class NodeResult:
    id: NodeResultId
    node_id: NodeId
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
        id_: NodeResultId,
        node_id: NodeId,
        workflow_id: WorkflowId,
        status: Status,
        stdout: str = "",
        stderr: str = "",
        artifact_uri: str = "",
        now: datetime,
    ) -> NodeResult:
        return cls(
            id=id_,
            node_id=node_id,
            workflow_id=workflow_id,
            status=status,
            stdout=stdout,
            stderr=stderr,
            artifact_uri=artifact_uri,
            created_at=now,
        )
