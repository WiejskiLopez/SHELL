"""SQL ORM model <-> domain entity mappers for Execution BC."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.domain.execution.aggregates.session_execution.session_execution import (
    SessionExecution,
)
from shell.domain.execution.aggregates.session_execution_state.session_execution_state import (
    SessionExecutionState,
)
from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
    TaskExecutionState,
)
from shell.domain.execution.aggregates.user_execution.user_execution import UserExecution
from shell.domain.execution.aggregates.user_execution_state.user_execution_state import (
    UserExecutionState,
)
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.aggregates.workflow.entities.node_execution_result import (
    NodeExecutionResult,
)
from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState
from shell.domain.execution.value_objects.artifact_uri import ArtifactUri
from shell.domain.execution.value_objects.execution_stderr import (
    ExecutionStderr,
)
from shell.domain.execution.value_objects.execution_stdout import (
    ExecutionStdout,
)
from shell.domain.execution.value_objects.graph_definition_id_ref import (
    GraphDefinitionIdRef,
)
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    NodeExecutionId,
    NodeExecutionResultId,
    SessionExecutionId,
    SessionExecutionStateId,
    SessionIdRef,
    TaskExecutionId,
    TaskExecutionStateId,
    UserExecutionId,
    UserExecutionStateId,
    WorkflowId,
)
from shell.domain.execution.value_objects.max_subgraph_depth import (
    MaxSubgraphDepth,
)
from shell.domain.execution.value_objects.task_execution_body import (
    TaskExecutionBody,
)
from shell.domain.execution.value_objects.task_name import TaskName
from shell.domain.execution.value_objects.user_id_ref import UserIdRef
from shell.domain.execution.value_objects.work_dir import WorkDir
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.domain.platform.value_objects.status import Status
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.infrastructure.execution.graph_execution_state.persistence.sql.models.graph_execution_state_input import (
    GraphExecutionStateInputModel,
)
from shell.infrastructure.execution.graph_execution_state.persistence.sql.models.graph_execution_state_output import (
    GraphExecutionStateOutputModel,
)
from shell.infrastructure.execution.persistence.sql.models import (
    GraphExecutionModel,
    NodeExecutionResultModel,
    SessionExecutionModel,
    SessionExecutionStateModel,
    TaskExecutionModel,
    TaskExecutionStateModel,
    UserExecutionModel,
    UserExecutionStateModel,
    WorkflowModel,
    WorkflowStateModel,
)
from shell.infrastructure.platform.context import get_correlation_id


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


def task_execution_model_to_entity(task_execution_model: TaskExecutionModel) -> TaskExecution:
    body = TaskExecutionBody(task_execution_model.body) if task_execution_model.body else None
    return TaskExecution(
        id=TaskExecutionId(task_execution_model.id),
        name=TaskName(task_execution_model.name),
        body=body,
        created_at=CreatedAt.from_datetime(_ensure_utc(task_execution_model.created_at)),
        work_dir=WorkDir(task_execution_model.work_dir or ""),
        workflow_id=(
            WorkflowId(task_execution_model.workflow_id)
            if task_execution_model.workflow_id
            else None
        ),
        deleted_at=(
            DeletedAt.from_datetime(task_execution_model.deleted_at)
            if task_execution_model.deleted_at
            else None
        ),
    )


def _created_at_value(dt: CreatedAt | DeletedAt | datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.value if hasattr(dt, "value") else dt


def task_execution_entity_to_model(task_execution: TaskExecution) -> TaskExecutionModel:
    return TaskExecutionModel(
        id=task_execution.id.value,
        name=task_execution.name.value,
        body=task_execution.body.value if task_execution.body else "",
        work_dir=task_execution.work_dir.value if task_execution.work_dir else "",
        created_at=_created_at_value(task_execution.created_at),
        workflow_id=task_execution.workflow_id.value if task_execution.workflow_id else None,
        deleted_at=_created_at_value(task_execution.deleted_at),
    )


def task_execution_update_model(model: TaskExecutionModel, entity: TaskExecution) -> None:
    model.status = entity.status.value if hasattr(entity.status, "value") else entity.status
    model.name = entity.name.value
    model.body = entity.body.value if entity.body else model.body
    model.work_dir = entity.work_dir.value if entity.work_dir else ""
    model.workflow_id = entity.workflow_id.value if entity.workflow_id else None
    model.created_at = _created_at_value(entity.created_at)  # type: ignore[assignment]
    model.deleted_at = _created_at_value(entity.deleted_at)


# ---------------------------------------------------------------------------
# TaskExecution State
# ---------------------------------------------------------------------------


def task_execution_state_model_to_entity(
    model: TaskExecutionStateModel,
) -> TaskExecutionState:
    return TaskExecutionState(
        id=TaskExecutionStateId(model.id),
        task_execution_id=TaskExecutionId(model.task_execution_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def task_execution_state_entity_to_model(
    entity: TaskExecutionState,
) -> TaskExecutionStateModel:
    return TaskExecutionStateModel(
        id=entity.id.value,
        task_execution_id=entity.task_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        created_at=entity.created_at.value if entity.created_at else None,
    )


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


def graph_execution_model_to_entity(graph_execution_model: GraphExecutionModel) -> GraphExecution:
    return GraphExecution(
        id=GraphExecutionId(graph_execution_model.id),
        task_execution_id=TaskExecutionId(graph_execution_model.task_execution_id),
        parent_graph_execution_id=(
            GraphExecutionId(graph_execution_model.parent_graph_execution_id)
            if graph_execution_model.parent_graph_execution_id
            else None
        ),
        depth=GraphDepth(graph_execution_model.depth),
        max_subgraph_depth=MaxSubgraphDepth(graph_execution_model.max_subgraph_depth),
        graph_definition_id=GraphDefinitionIdRef(graph_execution_model.graph_definition_id)
        if graph_execution_model.graph_definition_id
        else None,
        created_at=CreatedAt.from_datetime(_ensure_utc(graph_execution_model.created_at))
        if graph_execution_model.created_at
        else None,
        updated_at=UpdatedAt.from_datetime(_ensure_utc(graph_execution_model.updated_at))
        if graph_execution_model.updated_at
        else None,
        deleted_at=(
            DeletedAt.from_datetime(graph_execution_model.deleted_at)
            if graph_execution_model.deleted_at
            else None
        ),
    )


def graph_execution_update_model(model: GraphExecutionModel, entity: GraphExecution) -> None:
    model.status = entity.status.value if hasattr(entity.status, "value") else str(entity.status)
    model.parent_graph_execution_id = (
        entity.parent_graph_execution_id.value if entity.parent_graph_execution_id else None
    )
    model.depth = entity.depth.value
    model.graph_definition_id = entity.graph_definition_id.value
    model.updated_at = entity.updated_at.value if entity.updated_at else None
    model.deleted_at = _created_at_value(entity.deleted_at)


def graph_execution_entity_to_model(
    graph_execution: GraphExecution,
) -> GraphExecutionModel:
    graph_execution_model = GraphExecutionModel(
        id=graph_execution.id.value,
        task_execution_id=graph_execution.task_execution_id.value,
        graph_definition_id=graph_execution.graph_definition_id.value,
        parent_graph_execution_id=(
            graph_execution.parent_graph_execution_id.value
            if graph_execution.parent_graph_execution_id
            else None
        ),
        state_input={},
        state_output={},
        depth=graph_execution.depth.value if graph_execution.depth else 0,
        max_subgraph_depth=graph_execution.max_subgraph_depth.value
        if graph_execution.max_subgraph_depth
        else 5,
        timeout_at=None,
        correlation_id=get_correlation_id(),
        tags={},
        created_at=graph_execution.created_at.value if graph_execution.created_at else None,
        updated_at=graph_execution.updated_at.value if graph_execution.updated_at else None,
        deleted_at=_created_at_value(graph_execution.deleted_at),
    )
    return graph_execution_model


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# NodeExecutionResult
# ---------------------------------------------------------------------------


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


# ── GraphExecutionState ───────────────────────────────────────────────────────


def graph_execution_state_input_model_to_entity(
    model: GraphExecutionStateInputModel,
) -> GraphExecutionState:
    return GraphExecutionState(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        direction=StateDirection.IN,
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def graph_execution_state_input_entity_to_model(
    entity: GraphExecutionState,
) -> GraphExecutionStateInputModel:
    return GraphExecutionStateInputModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        state_data=entity.state_data,
        created_at=entity.created_at.value,
    )


# ── GraphExecutionStateOutput ─────────────────────────────────────────────────


def graph_execution_state_output_model_to_entity(
    model: GraphExecutionStateOutputModel,
) -> GraphExecutionState:
    return GraphExecutionState(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        direction=StateDirection.OUT,
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def graph_execution_state_output_entity_to_model(
    entity: GraphExecutionState,
) -> GraphExecutionStateOutputModel:
    return GraphExecutionStateOutputModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        state_data=entity.state_data,
        created_at=entity.created_at.value,
    )


# ── WorkflowState ──────────────────────────────────────────────────────────────


def workflow_state_model_to_entity(model: WorkflowStateModel) -> WorkflowState:
    return WorkflowState.restore(
        id=WorkflowStateId(model.id),
        workflow_id=WorkflowId(model.workflow_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def workflow_state_entity_to_model(entity: WorkflowState) -> WorkflowStateModel:
    return WorkflowStateModel(
        id=entity.id.value,
        workflow_id=entity.workflow_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        created_at=entity.created_at.value if entity.created_at else None,
    )


# ── UserExecution ─────────────────────────────────────────────────────────────


def user_execution_model_to_entity(model: UserExecutionModel) -> UserExecution:
    return UserExecution.restore(
        id=UserExecutionId(model.id),
        user_id=UserIdRef(model.user_id) if model.user_id else None,
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def user_execution_entity_to_model(entity: UserExecution) -> UserExecutionModel:
    return UserExecutionModel(
        id=entity.id.value,
        user_id=entity.user_id.value if entity.user_id else None,
        created_at=entity.created_at.value if entity.created_at else None,
    )


def user_execution_update_model(model: UserExecutionModel, entity: UserExecution) -> None:
    model.user_id = entity.user_id.value if entity.user_id else None
    assert entity.created_at is not None
    model.created_at = entity.created_at.value


# ── UserExecution State ────────────────────────────────────────────────────────


def user_execution_state_model_to_entity(model: UserExecutionStateModel) -> UserExecutionState:
    return UserExecutionState.restore(
        id=UserExecutionStateId(model.id),
        user_execution_id=UserExecutionId(model.user_execution_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def user_execution_state_entity_to_model(entity: UserExecutionState) -> UserExecutionStateModel:
    return UserExecutionStateModel(
        id=entity.id.value,
        user_execution_id=entity.user_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        created_at=entity.created_at.value if entity.created_at else None,
    )


# ── SessionExecution ───────────────────────────────────────────────────────────


def session_execution_model_to_entity(model: SessionExecutionModel) -> SessionExecution:
    return SessionExecution.restore(
        id=SessionExecutionId(model.id),
        user_execution_id=(
            UserExecutionId(model.user_execution_id) if model.user_execution_id else None
        ),
        session_id=SessionIdRef(model.session_id) if model.session_id else None,
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def session_execution_entity_to_model(entity: SessionExecution) -> SessionExecutionModel:
    return SessionExecutionModel(
        id=entity.id.value,
        user_execution_id=entity.user_execution_id.value if entity.user_execution_id else None,
        session_id=entity.session_id.value if entity.session_id else None,
        created_at=entity.created_at.value if entity.created_at else None,
    )


def session_execution_update_model(model: SessionExecutionModel, entity: SessionExecution) -> None:
    model.user_execution_id = entity.user_execution_id.value if entity.user_execution_id else None
    model.session_id = entity.session_id.value if entity.session_id else None
    assert entity.created_at is not None
    model.created_at = entity.created_at.value


# ── SessionExecution State ─────────────────────────────────────────────────────


def session_execution_state_model_to_entity(
    model: SessionExecutionStateModel,
) -> SessionExecutionState:
    return SessionExecutionState.restore(
        id=SessionExecutionStateId(model.id),
        session_execution_id=SessionExecutionId(model.session_execution_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def session_execution_state_entity_to_model(
    entity: SessionExecutionState,
) -> SessionExecutionStateModel:
    return SessionExecutionStateModel(
        id=entity.id.value,
        session_execution_id=entity.session_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        created_at=entity.created_at.value if entity.created_at else None,
    )
