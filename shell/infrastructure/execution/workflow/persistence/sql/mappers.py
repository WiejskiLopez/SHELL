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
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.status import Status
from shell.infrastructure.execution.node_execution.persistence.sql.models import (
    NodeExecutionResultModel,
)
from shell.infrastructure.execution.workflow.persistence.sql.models import WorkflowModel


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _created_at_value(dt: CreatedAt | DeletedAt | datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.value if hasattr(dt, "value") else dt


def workflow_model_to_entity(workflow_model: WorkflowModel) -> Workflow:
    return Workflow(
        id=WorkflowId(workflow_model.id),
        status=WorkflowStatus(workflow_model.status),
        session_id=SessionIdRef(workflow_model.session_id) if workflow_model.session_id else None,
        created_at=CreatedAt.from_datetime(workflow_model.created_at),
        deleted_at=(
            DeletedAt.from_datetime(workflow_model.deleted_at)
            if workflow_model.deleted_at
            else None
        ),
    )


def workflow_entity_to_model(work_flow: Workflow) -> WorkflowModel:
    return WorkflowModel(
        id=work_flow.id.value,
        status=work_flow.status.value,
        session_id=work_flow.session_id.value if work_flow.session_id else None,
        created_at=work_flow.created_at.value,
        deleted_at=_created_at_value(work_flow.deleted_at),
    )


def workflow_update_model(model: WorkflowModel, entity: Workflow) -> None:
    model.status = entity.status.value if hasattr(entity.status, "value") else entity.status
    model.session_id = entity.session_id.value if entity.session_id else None
    model.created_at = entity.created_at.value


def node_execution_result_model_to_entity(
    result_model: NodeExecutionResultModel,
) -> NodeExecutionResult:
    return NodeExecutionResult(
        id=NodeExecutionResultId(result_model.id),
        node_execution_id=NodeExecutionId(result_model.node_execution_id),
        workflow_id=WorkflowId(result_model.workflow_id),
        status=Status(result_model.status),
        stdout=ExecutionStdout(result_model.stdout),
        stderr=ExecutionStderr(result_model.stderr),
        artifact_uri=ArtifactUri(result_model.artifact_uri),
        created_at=CreatedAt.from_datetime(_ensure_utc(result_model.created_at)),
    )


def node_execution_result_entity_to_model(
    node_execution_result: NodeExecutionResult,
) -> NodeExecutionResultModel:
    return NodeExecutionResultModel(
        id=node_execution_result.id.value,
        node_execution_id=node_execution_result.node_execution_id.value,
        workflow_id=node_execution_result.workflow_id.value,
        status=node_execution_result.status.value,
        stdout=node_execution_result.stdout,
        stderr=node_execution_result.stderr,
        artifact_uri=node_execution_result.artifact_uri,
        created_at=node_execution_result.created_at,
    )
