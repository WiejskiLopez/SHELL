from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.value_objects.node_execution_result_id import (
    NodeExecutionResultId,
)
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.execution.value_objects.artifact_uri import ArtifactUri
    from shell.domain.execution.value_objects.execution_stderr import ExecutionStderr
    from shell.domain.execution.value_objects.execution_stdout import ExecutionStdout
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.platform.value_objects.status import Status


class NodeExecutionResult(Entity[NodeExecutionResultId]):
    __slots__ = (
        "_node_execution_id",
        "_workflow_id",
        "_status",
        "_stdout",
        "_stderr",
        "_artifact_uri",
        "_created_at",
    )

    def __init__(
        self,
        id: NodeExecutionResultId,
        node_execution_id: NodeExecutionId,
        workflow_id: WorkflowId,
        status: Status,
        created_at: CreatedAt,
        stdout: ExecutionStdout | None = None,
        stderr: ExecutionStderr | None = None,
        artifact_uri: ArtifactUri | None = None,
    ) -> None:
        super().__init__(id)
        self._node_execution_id = node_execution_id
        self._workflow_id = workflow_id
        self._status = status
        self._stdout = stdout
        self._stderr = stderr
        self._artifact_uri = artifact_uri
        self._created_at = created_at

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self._node_execution_id

    @property
    def workflow_id(self) -> WorkflowId:
        return self._workflow_id

    @property
    def status(self) -> Status:
        return self._status

    @property
    def stdout(self) -> ExecutionStdout | None:
        return self._stdout

    @property
    def stderr(self) -> ExecutionStderr | None:
        return self._stderr

    @property
    def artifact_uri(self) -> ArtifactUri | None:
        return self._artifact_uri

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @classmethod
    def new(
        cls,
        *,
        id_: NodeExecutionResultId,
        node_execution_id: NodeExecutionId,
        workflow_id: WorkflowId,
        status: Status,
        stdout: ExecutionStdout | None = None,
        stderr: ExecutionStderr | None = None,
        artifact_uri: ArtifactUri | None = None,
        now: CreatedAt,
    ) -> NodeExecutionResult:
        return cls(
            id=id_,
            node_execution_id=node_execution_id,
            workflow_id=workflow_id,
            status=status,
            stdout=stdout,
            stderr=stderr,
            artifact_uri=artifact_uri,
            created_at=now,
        )
