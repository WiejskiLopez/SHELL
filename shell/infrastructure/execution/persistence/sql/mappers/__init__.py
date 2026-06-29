"""SQL ORM model <-> domain entity mappers for Execution BC."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_node_transition_definition.graph_node_transition_definition import (
    GraphNodeTransitionDefinition,
)
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
    GraphNodeDefinitionId,
)
from shell.domain.definition.aggregates.graph_node_transition_definition.value_objects.graph_node_transition_definition_id import (
    GraphNodeTransitionDefinitionId,
)
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.value_objects.transition_definition import (
    TransitionDefinition,
)
from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
    TaskExecutionState,
)
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.aggregates.workflow.entities.graph_node_execution_result import (
    GraphNodeExecutionResult,
)
from shell.domain.execution.value_objects.artifact_uri import ArtifactUri
from shell.domain.execution.value_objects.edge_type import EdgeType
from shell.domain.execution.value_objects.execution_stderr import ExecutionStderr
from shell.domain.execution.value_objects.execution_stdout import ExecutionStdout
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.graph_execution_initialization_status import (
    GraphExecutionInitializationStatus,
)
from shell.domain.execution.value_objects.graph_node_definition_execution_slot import (
    GraphNodeDefinitionExecutionSlot,
)
from shell.domain.execution.value_objects.graph_node_definition_id import (
    GraphNodeDefinitionId as ExecutionGraphNodeDefinitionId,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    GraphNodeExecutionResultId,
    SessionExecutionId,
    SessionExecutionStateId,
    SessionIdRef,
    TaskExecutionId,
    TaskExecutionStateId,
    UserExecutionId,
    UserExecutionStateId,
    WorkflowId,
)
from shell.domain.execution.value_objects.is_current import IsCurrent
from shell.domain.execution.value_objects.max_iterations import MaxIterations
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.execution.value_objects.task_name import TaskName
from shell.domain.execution.value_objects.user_id_ref import UserIdRef
from shell.domain.execution.value_objects.work_dir import WorkDir
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.definition.value_objects.condition_language import ConditionLanguage
from shell.domain.definition.value_objects.data_mapping import DataMapping
from shell.domain.definition.value_objects.max_loop_count import MaxLoopCount
from shell.domain.definition.value_objects.retry_count import RetryCount
from shell.domain.definition.value_objects.transition_label import TransitionLabel
from shell.domain.definition.value_objects.transition_priority import TransitionPriority
from shell.domain.definition.value_objects.transition_retry_delay import TransitionRetryDelay
from shell.domain.definition.value_objects.transition_timeout_seconds import TransitionTimeoutSeconds
from shell.domain.platform.value_objects.condition_expression import ConditionExpression
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.domain.platform.value_objects.status import Status
from shell.infrastructure.definition.persistence.sql.models import (
    GraphNodeTransitionDefinitionModel,
)
from shell.infrastructure.execution.persistence.sql.models import (
    GraphExecutionModel,
    GraphNodeExecutionResultModel,
    GraphNodeTransitionExecutionModel,
    SessionExecutionModel,
    SessionExecutionStateModel,
    TaskExecutionModel,
    TaskExecutionStateModel,
    UserExecutionModel,
    UserExecutionStateModel,
    WorkflowModel,
    WorkflowStateModel,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )
    from shell.domain.execution.aggregates.session_execution.session_execution import (
        SessionExecution,
    )
    from shell.domain.execution.aggregates.session_execution_state.session_execution_state import (
        SessionExecutionState,
    )
    from shell.domain.execution.aggregates.user_execution.user_execution import UserExecution
    from shell.domain.execution.aggregates.user_execution_state.user_execution_state import (
        UserExecutionState,
    )
    from shell.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState
    from shell.infrastructure.execution.persistence.sql.models.graph_execution_state_input import (
        GraphExecutionStateInputModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.graph_execution_state_output import (
        GraphExecutionStateOutputModel,
    )


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


def task_execution_model_to_entity(task_execution_model: TaskExecutionModel) -> TaskExecution:
    return TaskExecution(
        id=TaskExecutionId(task_execution_model.id),
        name=TaskName(task_execution_model.name),
        created_at=CreatedAt.from_datetime(_ensure_utc(task_execution_model.created_at)),
        work_dir=WorkDir(task_execution_model.work_dir or ""),
        workflow_id=(
            WorkflowId(task_execution_model.workflow_id)
            if task_execution_model.workflow_id
            else None
        ),
    )


def _created_at_value(dt: CreatedAt | datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.value if hasattr(dt, "value") else dt


def task_execution_entity_to_model(task_execution: TaskExecution) -> TaskExecutionModel:
    return TaskExecutionModel(
        id=task_execution.id.value,
        name=task_execution.name.value,
        work_dir=task_execution.work_dir.value if task_execution.work_dir else "",
        created_at=_created_at_value(task_execution.created_at),
        workflow_id=task_execution.workflow_id.value if task_execution.workflow_id else None,
    )


def task_execution_update_model(model: TaskExecutionModel, entity: TaskExecution) -> None:
    model.status = entity.status.value if hasattr(entity.status, 'value') else entity.status
    model.name = entity.name.value
    model.work_dir = entity.work_dir.value if entity.work_dir else ""
    model.workflow_id = entity.workflow_id.value if entity.workflow_id else None
    model.created_at = _created_at_value(entity.created_at)


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
        is_current=IsCurrent(model.is_current),
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
        is_current=entity.is_current.value,
        created_at=entity.created_at.value if entity.created_at else None,
    )


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


def graph_execution_model_to_entity(graph_execution_model: GraphExecutionModel) -> GraphExecution:
    slots_raw = graph_execution_model.graph_node_definition_executions or {}
    slots = [
        GraphNodeDefinitionExecutionSlot(
            graph_node_definition_id=ExecutionGraphNodeDefinitionId(def_id),
            graph_node_execution_id=GraphNodeExecutionId(exec_id) if exec_id else None,
        )
        for def_id, exec_id in slots_raw.items()
    ]
    return GraphExecution(
        id=GraphExecutionId(graph_execution_model.id),
        task_execution_id=TaskExecutionId(graph_execution_model.task_execution_id),
        parent_graph_execution_id=(
            GraphExecutionId(graph_execution_model.parent_graph_execution_id)
            if graph_execution_model.parent_graph_execution_id
            else None
        ),
        depth=GraphDepth(graph_execution_model.depth),
        initialization_status=GraphExecutionInitializationStatus(graph_execution_model.initialization_status) if graph_execution_model.initialization_status else None,
        graph_node_definition_execution_slots=slots,
    )


def transition_definition_model_to_entity(
    model: GraphNodeTransitionExecutionModel,
) -> TransitionDefinition:
    return TransitionDefinition(
        source_node_execution_id=model.source_node_execution_id or "",
        target_node_execution_id=model.target_node_execution_id,
        edge_type=EdgeType(model.transition_type.upper()),
        priority=model.priority,
        condition_expression=model.condition_expression,
        condition_language=model.condition_language,
        max_iterations=model.max_loop_count,
        timeout_seconds=model.timeout_seconds,
        retry_count=model.retry_count,
        retry_delay_seconds=model.retry_delay_seconds,
        data_mapping=dict(model.data_mapping) if model.data_mapping else None,
        label=model.label,
    )


def transition_definition_entity_to_model(
    transition: TransitionDefinition,
    graph_execution_id: str,
    now: datetime,
) -> GraphNodeTransitionExecutionModel:
    return GraphNodeTransitionExecutionModel(
        id=f"{graph_execution_id}_{transition.source_node_execution_id}_{transition.target_node_execution_id or 'none'}_{transition.edge_type.value}",
        graph_execution_id=graph_execution_id,
        source_node_execution_id=transition.source_node_execution_id,
        target_node_execution_id=transition.target_node_execution_id,
        transition_type=transition.edge_type.value,
        priority=transition.priority,
        condition_expression=transition.condition_expression,
        condition_language=transition.condition_language,
        max_loop_count=transition.max_iterations,
        timeout_seconds=transition.timeout_seconds,
        retry_count=transition.retry_count,
        retry_delay_seconds=transition.retry_delay_seconds,
        data_mapping=transition.data_mapping,
        label=transition.label,
        created_at=now,
        updated_at=now,
    )


def graph_node_transition_definition_model_to_entity(
    model: GraphNodeTransitionDefinitionModel,
) -> GraphNodeTransitionDefinition:
    return GraphNodeTransitionDefinition(
        id=GraphNodeTransitionDefinitionId(model.id),
        graph_definition_id=GraphDefinitionId(model.graph_definition_id),
        source_node_definition_id=(
            GraphNodeDefinitionId(model.source_node_definition_id)
            if model.source_node_definition_id
            else None
        ),
        target_node_definition_id=GraphNodeDefinitionId(model.target_node_definition_id),
        transition_type=EdgeType(model.transition_type.upper()),
        priority=TransitionPriority(model.priority),
        condition_expression=ConditionExpression(model.condition_expression) if model.condition_expression else None,
        condition_language=ConditionLanguage(model.condition_language) if model.condition_language else None,
        max_loop_count=MaxLoopCount(model.max_loop_count),
        timeout_seconds=TransitionTimeoutSeconds(model.timeout_seconds) if model.timeout_seconds is not None else None,
        retry_count=RetryCount(model.retry_count),
        retry_delay_seconds=TransitionRetryDelay(model.retry_delay_seconds),
        data_mapping=DataMapping(dict(model.data_mapping)) if model.data_mapping else None,
        label=TransitionLabel(model.label) if model.label else None,
    )


def graph_node_transition_definition_entity_to_model(
    transition: GraphNodeTransitionDefinition,
    now: datetime,
) -> GraphNodeTransitionDefinitionModel:
    return GraphNodeTransitionDefinitionModel(
        id=transition.id.value,
        graph_definition_id=transition.graph_definition_id.value,
        source_node_definition_id=(
            transition.source_node_definition_id.value
            if transition.source_node_definition_id
            else None
        ),
        target_node_definition_id=transition.target_node_definition_id.value,
        transition_type=transition.transition_type.value,
        priority=transition.priority,
        condition_expression=transition.condition_expression,
        condition_language=transition.condition_language,
        max_loop_count=transition.max_loop_count,
        timeout_seconds=transition.timeout_seconds,
        retry_count=transition.retry_count,
        retry_delay_seconds=transition.retry_delay_seconds,
        data_mapping=transition.data_mapping,
        label=transition.label,
        created_at=now,
        updated_at=now,
    )


def graph_execution_update_model(model: GraphExecutionModel, entity: GraphExecution) -> None:
    model.status = entity.status.value if hasattr(entity.status, 'value') else str(entity.status)
    model.initialization_status = entity.initialization_status.value if hasattr(entity.initialization_status, 'value') else str(entity.initialization_status)
    model.parent_graph_execution_id = entity.parent_graph_execution_id.value if entity.parent_graph_execution_id else None
    model.depth = entity.depth.value
    model.graph_node_definition_executions = {
        slot.graph_node_definition_id.value: slot.graph_node_execution_id.value if slot.graph_node_execution_id else None
        for slot in entity.graph_node_definition_execution_slots
    }


def graph_execution_entity_to_model(
    graph_execution: GraphExecution,
) -> GraphExecutionModel:
    from shell.infrastructure.platform.context import get_correlation_id

    graph_execution_model = GraphExecutionModel(
        id=graph_execution.id.value,
        task_execution_id=graph_execution.task_execution_id.value,
        graph_definition_id="",
        parent_graph_execution_id=(
            graph_execution.parent_graph_execution_id.value
            if graph_execution.parent_graph_execution_id
            else None
        ),
        initialization_status=graph_execution.initialization_status.value,
        graph_node_definition_executions={
            slot.graph_node_definition_id.value: slot.graph_node_execution_id.value if slot.graph_node_execution_id else None
            for slot in graph_execution.graph_node_definition_execution_slots
        },
        state_input={},
        state_output={},
        depth=graph_execution.depth.value if graph_execution.depth else 0,
        timeout_at=None,
        correlation_id=get_correlation_id(),
        tags={},
    )
    return graph_execution_model


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


def workflow_model_to_entity(workflow_model: WorkflowModel) -> Workflow:
    return Workflow(
        id=WorkflowId(workflow_model.id),
        status=WorkflowStatus(workflow_model.status),
        session_execution_id=(
            SessionExecutionId(workflow_model.session_execution_id)
            if workflow_model.session_execution_id
            else None
        ),
        session_id=SessionIdRef(workflow_model.session_id) if workflow_model.session_id else None,
        created_at=CreatedAt.from_datetime(workflow_model.created_at),
    )


def workflow_entity_to_model(work_flow: Workflow) -> WorkflowModel:
    return WorkflowModel(
        id=work_flow.id.value,
        status=work_flow.status.value,
        session_execution_id=(
            work_flow.session_execution_id.value
            if work_flow.session_execution_id
            else None
        ),
        session_id=work_flow.session_id.value if work_flow.session_id else None,
        created_at=work_flow.created_at.value,
    )


def workflow_update_model(model: WorkflowModel, entity: Workflow) -> None:
    model.status = entity.status.value if hasattr(entity.status, 'value') else entity.status
    model.session_execution_id = (
        entity.session_execution_id.value if entity.session_execution_id else None
    )
    model.session_id = entity.session_id.value if entity.session_id else None
    model.created_at = entity.created_at.value


# ---------------------------------------------------------------------------
# GraphNodeExecutionResult
# ---------------------------------------------------------------------------


def graph_node_execution_result_model_to_entity(
    result_model: GraphNodeExecutionResultModel,
) -> GraphNodeExecutionResult:
    return GraphNodeExecutionResult(
        id=GraphNodeExecutionResultId(result_model.id),
        graph_node_execution_id=GraphNodeExecutionId(result_model.graph_node_execution_id),
        workflow_id=WorkflowId(result_model.workflow_id),
        status=Status(result_model.status),
        stdout=ExecutionStdout(result_model.stdout),
        stderr=ExecutionStderr(result_model.stderr),
        artifact_uri=ArtifactUri(result_model.artifact_uri),
        created_at=CreatedAt.from_datetime(_ensure_utc(result_model.created_at)),
    )


def graph_node_execution_result_entity_to_model(
    graph_node_execution_result: GraphNodeExecutionResult,
) -> GraphNodeExecutionResultModel:
    return GraphNodeExecutionResultModel(
        id=graph_node_execution_result.id.value,
        graph_node_execution_id=graph_node_execution_result.graph_node_execution_id.value,
        workflow_id=graph_node_execution_result.workflow_id.value,
        status=graph_node_execution_result.status.value,
        stdout=graph_node_execution_result.stdout,
        stderr=graph_node_execution_result.stderr,
        artifact_uri=graph_node_execution_result.artifact_uri,
        created_at=graph_node_execution_result.created_at,
    )


# ── GraphExecutionState ───────────────────────────────────────────────────────


def graph_execution_state_input_model_to_entity(model: GraphExecutionStateInputModel) -> GraphExecutionState:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )
    from shell.domain.platform.value_objects.state_direction import StateDirection

    return GraphExecutionState(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        direction=StateDirection.IN,
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        is_current=IsCurrent(model.is_current),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def graph_execution_state_input_entity_to_model(entity: GraphExecutionState) -> GraphExecutionStateInputModel:
    return GraphExecutionStateInputModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        state_data=entity.state_data,
        is_current=entity.is_current.value,
        created_at=entity.created_at.value,
    )


# ── GraphExecutionStateOutput ─────────────────────────────────────────────────


def graph_execution_state_output_model_to_entity(model: GraphExecutionStateOutputModel) -> GraphExecutionState:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )
    from shell.domain.platform.value_objects.state_direction import StateDirection

    return GraphExecutionState(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        direction=StateDirection.OUT,
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        is_current=IsCurrent(model.is_current),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def graph_execution_state_output_entity_to_model(entity: GraphExecutionState) -> GraphExecutionStateOutputModel:
    return GraphExecutionStateOutputModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        state_data=entity.state_data,
        is_current=entity.is_current.value,
        created_at=entity.created_at.value,
    )


# ── WorkflowState ──────────────────────────────────────────────────────────────


def workflow_state_model_to_entity(model: WorkflowStateModel) -> WorkflowState:
    from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
        WorkflowStateId,
    )
    from shell.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState

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
        is_current=True,
        created_at=entity.created_at.value if entity.created_at else None,
    )


# ── UserExecution ─────────────────────────────────────────────────────────────


def user_execution_model_to_entity(model: UserExecutionModel) -> UserExecution:
    from shell.domain.execution.aggregates.user_execution.user_execution import UserExecution

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
    from shell.domain.execution.aggregates.user_execution_state.user_execution_state import (
        UserExecutionState,
    )

    return UserExecutionState.restore(
        id=UserExecutionStateId(model.id),
        user_execution_id=UserExecutionId(model.user_execution_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        is_current=IsCurrent(model.is_current),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def user_execution_state_entity_to_model(entity: UserExecutionState) -> UserExecutionStateModel:
    return UserExecutionStateModel(
        id=entity.id.value,
        user_execution_id=entity.user_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        is_current=entity.is_current.value,
        created_at=entity.created_at.value if entity.created_at else None,
    )


# ── SessionExecution ───────────────────────────────────────────────────────────


def session_execution_model_to_entity(model: SessionExecutionModel) -> SessionExecution:
    from shell.domain.execution.aggregates.session_execution.session_execution import (
        SessionExecution,
    )
    from shell.domain.execution.value_objects.session_id_ref import SessionIdRef

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


def session_execution_state_model_to_entity(model: SessionExecutionStateModel) -> SessionExecutionState:
    from shell.domain.execution.aggregates.session_execution_state.session_execution_state import (
        SessionExecutionState,
    )

    return SessionExecutionState.restore(
        id=SessionExecutionStateId(model.id),
        session_execution_id=SessionExecutionId(model.session_execution_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        is_current=IsCurrent(model.is_current),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def session_execution_state_entity_to_model(entity: SessionExecutionState) -> SessionExecutionStateModel:
    return SessionExecutionStateModel(
        id=entity.id.value,
        session_execution_id=entity.session_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        is_current=entity.is_current.value,
        created_at=entity.created_at.value if entity.created_at else None,
    )
