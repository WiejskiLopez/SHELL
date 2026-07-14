"""SQL ORM model <-> domain entity mappers for Workflow aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.domain.execution.aggregates.workflow import Workflow
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
from shell.domain.execution.aggregates.workflow.value_objects.workflow_status import WorkflowStatus
from shell.infrastructure.execution.node_execution.persistence.sql.models import (
    NodeExecutionResultModel,
)
from shell.infrastructure.execution.workflow.persistence.sql.models import WorkflowModel
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.status import Status


def workflow_entity_to_model(work_flow: Workflow) -> WorkflowModel:
    return WorkflowModel(
        id=work_flow.id.value,
        status=work_flow.status.value,
        session_id=work_flow.session_id.value if work_flow.session_id else None,
        created_at=work_flow.created_at.value,
        deleted_at=_created_at_value(work_flow.deleted_at),
    )

