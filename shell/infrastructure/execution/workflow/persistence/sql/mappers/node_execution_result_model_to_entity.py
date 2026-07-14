"""SQL ORM model <-> domain entity mappers for Workflow aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_status import (
    NodeExecutionStatus,
)
from shell.domain.execution.aggregates.workflow.entities.node_execution_result import (
    NodeExecutionResult,
)
from shell.domain.execution.aggregates.workflow.value_objects.artifact_uri import ArtifactUri
from shell.domain.execution.aggregates.workflow.value_objects.execution_stderr import (
    ExecutionStderr,
)
from shell.domain.execution.aggregates.workflow.value_objects.execution_stdout import (
    ExecutionStdout,
)
from shell.domain.execution.aggregates.workflow.value_objects.node_execution_result_id import (
    NodeExecutionResultId,
)
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)

if TYPE_CHECKING:
    from shell.infrastructure.execution.node_execution.persistence.sql.models import (
        NodeExecutionResultModel,
    )


def node_execution_result_model_to_entity(
    result_model: NodeExecutionResultModel,
) -> NodeExecutionResult:
    return NodeExecutionResult(
        id=NodeExecutionResultId(result_model.id),
        node_execution_id=NodeExecutionId(result_model.node_execution_id),
        workflow_id=WorkflowId(result_model.workflow_id),
        status=NodeExecutionStatus(result_model.status),
        stdout=ExecutionStdout(result_model.stdout),
        stderr=ExecutionStderr(result_model.stderr),
        artifact_uri=ArtifactUri(result_model.artifact_uri),
        created_at=CreatedAt.from_datetime(_ensure_utc(result_model.created_at)),
    )
