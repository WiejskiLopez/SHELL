"""SQL ORM model <-> domain entity mappers."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.definition.aggregates.rag_document import RagChunk, RagDocument
from shell.domain.definition.entities.graph_definition import GraphDefinition
from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
from shell.domain.definition.entities.graph_node_transition_definition import (
    GraphNodeTransitionDefinition,
)
from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.definition.value_objects.ids import (
    GraphDefinitionId,
    GraphNodeDefinitionId,
    GraphNodeTransitionDefinitionId,
    RagChunkId,
    RagDocumentId,
    RunnerConfigId,
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
from shell.domain.execution.value_objects.edge_type import EdgeType
from shell.domain.execution.value_objects.environment import Environment
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
    SessionId,
    TaskExecutionId,
    TaskExecutionStateId,
    UserExecutionId,
    UserExecutionStateId,
    WorkflowId,
)
from shell.domain.execution.value_objects.is_current import IsCurrent
from shell.domain.execution.value_objects.max_iterations import MaxIterations
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.execution.value_objects.state_direction import StateDirection
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.execution.value_objects.work_dir import WorkDir
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.hash import Hash
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.platform.value_objects.status import Status
from shell.domain.session.aggregates.session import Session
from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel,
    GraphNodeDefinitionModel,
    GraphNodeTransitionDefinitionModel,
    RagChunkModel,
    RagDocumentModel,
    RunnerConfigModel,
)
from shell.infrastructure.execution.persistence.sql.models import (
    GraphExecutionModel,
    GraphNodeExecutionResultModel,
    GraphNodeTransitionExecutionModel,
    SessionExecutionModel,
    SessionExecutionStateModel,
    SessionModel,
    TaskExecutionModel,
    TaskExecutionStateModel,
    UserExecutionModel,
    UserExecutionStateModel,
    WorkflowModel,
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
        name=TaskExecutionName(task_execution_model.name),
        created_at=_ensure_utc(task_execution_model.created_at),
        work_dir=task_execution_model.work_dir or "",
        workflow_id=(
            WorkflowId(task_execution_model.workflow_id)
            if task_execution_model.workflow_id
            else None
        ),
    )


def task_execution_entity_to_model(task_execution: TaskExecution) -> TaskExecutionModel:
    return TaskExecutionModel(
        id=task_execution.id.value,
        name=task_execution.name.value,
        work_dir=task_execution.work_dir.value if hasattr(task_execution.work_dir, 'value') else task_execution.work_dir or "",
        created_at=task_execution.created_at,
        workflow_id=task_execution.workflow_id.value if task_execution.workflow_id else None,
    )


def task_execution_update_model(model: TaskExecutionModel, entity: TaskExecution) -> None:
    model.status = entity.status.value if hasattr(entity.status, 'value') else entity.status
    model.name = entity.name.value if hasattr(entity.name, 'value') else entity.name
    model.work_dir = entity.work_dir.value if hasattr(entity.work_dir, 'value') else (entity.work_dir or "")
    model.workflow_id = entity.workflow_id.value if entity.workflow_id else None
    model.created_at = entity.created_at


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
        depth=graph_execution_model.depth,
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
        max_iterations=MaxIterations(model.max_loop_count),
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
        max_loop_count=transition.max_iterations.value if transition.max_iterations else None,
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
        priority=model.priority,
        condition_expression=model.condition_expression,
        condition_language=model.condition_language,
        max_loop_count=model.max_loop_count,
        timeout_seconds=model.timeout_seconds,
        retry_count=model.retry_count,
        retry_delay_seconds=model.retry_delay_seconds,
        data_mapping=dict(model.data_mapping) if model.data_mapping else None,
        label=model.label,
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
    model.depth = entity.depth.value if hasattr(entity.depth, 'value') else entity.depth
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
        session_id=SessionId(workflow_model.session_id) if workflow_model.session_id else None,
        created_at=_ensure_utc(workflow_model.created_at),
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
        created_at=work_flow.created_at,
    )


def workflow_update_model(model: WorkflowModel, entity: Workflow) -> None:
    model.status = entity.status.value if hasattr(entity.status, 'value') else entity.status
    model.session_execution_id = (
        entity.session_execution_id.value if entity.session_execution_id else None
    )
    model.session_id = entity.session_id.value if entity.session_id else None
    model.created_at = entity.created_at


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
        stdout=result_model.stdout,
        stderr=result_model.stderr,
        artifact_uri=result_model.artifact_uri,
        created_at=_ensure_utc(result_model.created_at),
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


# ---------------------------------------------------------------------------
# RunnerConfig
# ---------------------------------------------------------------------------


def runner_config_model_to_entity(runner_config_model: RunnerConfigModel) -> RunnerConfig:
    return RunnerConfig(
        id=RunnerConfigId(runner_config_model.id),
        package_name=runner_config_model.package_name,
        kind=runner_config_model.kind,
        hash=Hash(runner_config_model.hash),
        body=dict(runner_config_model.body),
        created_at=_ensure_utc(runner_config_model.created_at),
    )


def runner_config_entity_to_model(runner_config: RunnerConfig) -> RunnerConfigModel:
    return RunnerConfigModel(
        id=runner_config.id.value,
        package_name=runner_config.package_name,
        kind=runner_config.kind,
        hash=runner_config.hash.value,
        body=runner_config.body,
        created_at=runner_config.created_at,
    )


def runner_config_update_model(model: RunnerConfigModel, entity: RunnerConfig) -> None:
    model.package_name = entity.package_name
    model.kind = entity.kind
    model.hash = entity.hash.value if hasattr(entity.hash, 'value') else entity.hash
    model.body = entity.body
    model.created_at = entity.created_at


# ---------------------------------------------------------------------------
# GraphDefinition
# ---------------------------------------------------------------------------


def graph_definition_model_to_entity(
    graph_definition_model: GraphDefinitionModel,
) -> GraphDefinition:
    return GraphDefinition(
        id=GraphDefinitionId(graph_definition_model.id),
        name=graph_definition_model.name,
        purpose=graph_definition_model.purpose,
        graph_node_definitions=[
            graph_node_definition_model_to_entity(node)
            for node in graph_definition_model.graph_node_execution_models
        ],
        transition_definitions=[
            graph_node_transition_definition_model_to_entity(t)
            for t in graph_definition_model.graph_node_transition_definition_models
        ],
    )


def graph_definition_entity_to_model(
    graph_definition: GraphDefinition,
) -> GraphDefinitionModel:
    graph_definition_model = GraphDefinitionModel(
        id=graph_definition.id,
        name=graph_definition.name,
        purpose=graph_definition.purpose,
    )
    graph_definition_model.graph_node_execution_models = [
        graph_node_definition_entity_to_model(
            node,
            graph_definition.id.value,
        )
        for node in graph_definition.graph_node_definitions
    ]
    _now = datetime.now(UTC)
    graph_definition_model.graph_node_transition_definition_models = [
        graph_node_transition_definition_entity_to_model(t, _now)
        for t in graph_definition.transition_definitions
    ]
    return graph_definition_model


def graph_definition_update_model(model: GraphDefinitionModel, entity: GraphDefinition) -> None:
    model.name = entity.name
    model.purpose = entity.purpose
    # Node definitions and transition definitions are managed separately


def graph_node_definition_model_to_entity(
    graph_node_definition_model: GraphNodeDefinitionModel,
) -> GraphNodeDefinition:
    return GraphNodeDefinition(
        id=GraphNodeDefinitionId(graph_node_definition_model.id),
        position=graph_node_definition_model.position,
        mode=Mode(graph_node_definition_model.mode),
        role=graph_node_definition_model.role,
        node_type=graph_node_definition_model.node_type,
        model=graph_node_definition_model.model or "",
        command=graph_node_definition_model.command,
        timeout=graph_node_definition_model.timeout,
        retries=graph_node_definition_model.retries,
        log_level=graph_node_definition_model.log_level,
        max_step=graph_node_definition_model.max_step,
        no_ask_user=bool(graph_node_definition_model.no_ask_user),
        autopilot=bool(graph_node_definition_model.autopilot),
        status_initial=graph_node_definition_model.status_initial,
        script=graph_node_definition_model.script or "",
        script_type=graph_node_definition_model.script_type or "",
    )


def graph_node_definition_entity_to_model(
    graph_node_definition: GraphNodeDefinition,
    graph_definition_id: str,
) -> GraphNodeDefinitionModel:
    return GraphNodeDefinitionModel(
        id=graph_node_definition.id.value,
        graph_definition_id=graph_definition_id,
        position=graph_node_definition.position,
        mode=graph_node_definition.mode.value,
        role=graph_node_definition.role,
        node_type=graph_node_definition.node_type,
        model=graph_node_definition.model,
        command=graph_node_definition.command,
        timeout=graph_node_definition.timeout,
        retries=graph_node_definition.retries,
        log_level=graph_node_definition.log_level,
        max_step=graph_node_definition.max_step,
        no_ask_user=graph_node_definition.no_ask_user,
        autopilot=graph_node_definition.autopilot,
        status_initial=graph_node_definition.status_initial,
        script=graph_node_definition.script,
        script_type=graph_node_definition.script_type,
    )


def graph_node_definition_update_model(model: GraphNodeDefinitionModel, entity: GraphNodeDefinition) -> None:
    model.position = entity.position
    model.mode = entity.mode.value if hasattr(entity.mode, 'value') else entity.mode
    model.role = entity.role
    model.node_type = entity.node_type
    model.model = entity.model or ""
    model.command = entity.command
    model.timeout = entity.timeout
    model.retries = entity.retries
    model.log_level = entity.log_level
    model.max_step = entity.max_step
    model.no_ask_user = bool(entity.no_ask_user) if entity.no_ask_user is not None else False
    model.autopilot = bool(entity.autopilot) if entity.autopilot is not None else False
    model.status_initial = entity.status_initial
    model.script = entity.script or ""
    model.script_type = entity.script_type or ""


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


def session_model_to_entity(session_model: SessionModel) -> Session:
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.platform.value_objects.updated_at import UpdatedAt
    from shell.domain.projekt.value_objects.project_id import ProjectId
    from shell.domain.user.value_objects.user_id import UserId

    return Session(
        id=SessionId(session_model.id),
        user_id=UserId(session_model.user_id),
        project_id=ProjectId(session_model.project_id),
        environment=Environment(
            os=session_model.environment_os,
            runtime=session_model.environment_runtime,
            cwd=session_model.environment_cwd,
        ),
        status=session_model.status,
        opened_at=CreatedAt.from_datetime(session_model.opened_at),
        closed_at=UpdatedAt.from_datetime(session_model.closed_at) if session_model.closed_at else None,
    )


def session_entity_to_model(session: Session) -> SessionModel:
    return SessionModel(
        id=session.id.value,
        goal=session.goal,
        status=session.status,
        user_id=session.user_id.value,
        project_id=session.project_id.value,
        environment_os=session.environment.os,
        environment_runtime=session.environment.runtime,
        environment_cwd=session.environment.cwd,
        opened_at=session.opened_at.value,
        closed_at=session.closed_at.value if session.closed_at is not None else None,
    )


def session_update_model(model: SessionModel, entity: Session) -> None:
    model.goal = entity.goal
    model.status = entity.status
    model.user_id = entity.user_id.value
    model.project_id = entity.project_id.value
    model.environment_os = entity.environment.os
    model.environment_runtime = entity.environment.runtime
    model.environment_cwd = entity.environment.cwd
    model.opened_at = entity.opened_at.value
    model.closed_at = entity.closed_at.value if entity.closed_at is not None else None


# ---------------------------------------------------------------------------
# RagDocument
# ---------------------------------------------------------------------------


def rag_document_model_to_entity(rag_document_model: RagDocumentModel) -> RagDocument:
    return RagDocument(
        id=RagDocumentId(rag_document_model.id),
        source_uri=rag_document_model.source_uri,
        title=rag_document_model.title,
        domain=rag_document_model.domain,
        created_at=_ensure_utc(rag_document_model.created_at),
        chunks=[
            rag_chunk_model_to_entity(c)
            for c in sorted(rag_document_model.chunks, key=lambda c: c.chunk_index)
        ],
    )


def rag_document_entity_to_model(rag_document: RagDocument) -> RagDocumentModel:
    model = RagDocumentModel(
        id=rag_document.id.value,
        source_uri=rag_document.source_uri,
        title=rag_document.title,
        domain=rag_document.domain,
        created_at=rag_document.created_at,
    )
    model.chunks = [rag_chunk_entity_to_model(c) for c in rag_document.chunks]
    return model


def rag_document_update_model(model: RagDocumentModel, entity: RagDocument) -> None:
    model.source_uri = entity.source_uri
    model.title = entity.title
    model.domain = entity.domain
    model.created_at = entity.created_at
    # Chunks are managed separately


# ---------------------------------------------------------------------------
# RagChunk
# ---------------------------------------------------------------------------


def rag_chunk_model_to_entity(rag_chunk_model: RagChunkModel) -> RagChunk:
    return RagChunk(
        id=RagChunkId(rag_chunk_model.id),
        document_id=RagDocumentId(rag_chunk_model.document_id),
        chunk_index=rag_chunk_model.chunk_index,
        chunk_text=rag_chunk_model.chunk_text,
        embedding=rag_chunk_model.embedding,
        embedding_model=rag_chunk_model.embedding_model,
    )


def rag_chunk_entity_to_model(rag_chunk: RagChunk) -> RagChunkModel:
    return RagChunkModel(
        id=rag_chunk.id.value,
        document_id=rag_chunk.document_id.value,
        chunk_index=rag_chunk.chunk_index,
        chunk_text=rag_chunk.chunk_text,
        embedding=rag_chunk.embedding,
        embedding_model=rag_chunk.embedding_model,
    )


# ── GraphExecutionState ───────────────────────────────────────────────────────


def graph_execution_state_input_model_to_entity(model):
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )
    from shell.domain.execution.value_objects.state_direction import StateDirection

    return GraphExecutionState(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        direction=StateDirection.IN,
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        is_current=IsCurrent(model.is_current),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def graph_execution_state_input_entity_to_model(entity):
    from shell.infrastructure.execution.persistence.sql.models.graph_execution_state_input import (
        GraphExecutionStateInputModel,
    )

    return GraphExecutionStateInputModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        state_data=entity.state_data.to_dict(),
        is_current=entity.is_current.value,
        created_at=entity.created_at.value if entity.created_at else None,
    )


# ── GraphExecutionStateOutput ─────────────────────────────────────────────────


def graph_execution_state_output_model_to_entity(model):
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )
    from shell.domain.execution.value_objects.state_direction import StateDirection

    return GraphExecutionState(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        direction=StateDirection.OUT,
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        is_current=IsCurrent(model.is_current),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def graph_execution_state_output_entity_to_model(entity):
    from shell.infrastructure.execution.persistence.sql.models.graph_execution_state_output import (
        GraphExecutionStateOutputModel,
    )

    return GraphExecutionStateOutputModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        state_data=entity.state_data.to_dict(),
        is_current=entity.is_current.value,
        created_at=entity.created_at.value if entity.created_at else None,
    )


# ── WorkflowState ──────────────────────────────────────────────────────────────


def workflow_state_model_to_entity(model):
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


def workflow_state_entity_to_model(entity):
    from shell.infrastructure.execution.persistence.sql.models.workflow_state import (
        WorkflowStateModel,
    )

    return WorkflowStateModel(
        id=entity.id.value,
        workflow_id=entity.workflow_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        is_current=True,
        created_at=entity.created_at.value if entity.created_at else None,
    )


# ── UserExecution ─────────────────────────────────────────────────────────────


def user_execution_model_to_entity(model: UserExecutionModel):
    from shell.domain.execution.aggregates.user_execution.user_execution import UserExecution
    from shell.domain.user.value_objects.user_id import UserId

    return UserExecution.restore(
        id=UserExecutionId(model.id),
        user_id=UserId(model.user_id) if model.user_id else None,
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def user_execution_entity_to_model(entity):
    return UserExecutionModel(
        id=entity.id.value,
        user_id=entity.user_id.value if entity.user_id else None,
        created_at=entity.created_at.value if entity.created_at else None,
    )


def user_execution_update_model(model: UserExecutionModel, entity) -> None:
    model.user_id = entity.user_id.value if entity.user_id else None
    model.created_at = entity.created_at.value if entity.created_at else None


# ── UserExecution State ────────────────────────────────────────────────────────


def user_execution_state_model_to_entity(model: UserExecutionStateModel):
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


def user_execution_state_entity_to_model(entity):
    return UserExecutionStateModel(
        id=entity.id.value,
        user_execution_id=entity.user_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        is_current=entity.is_current.value,
        created_at=entity.created_at.value if entity.created_at else None,
    )


# ── SessionExecution ───────────────────────────────────────────────────────────


def session_execution_model_to_entity(model: SessionExecutionModel):
    from shell.domain.execution.aggregates.session_execution.session_execution import (
        SessionExecution,
    )
    from shell.domain.session.aggregates.session.value_objects.session_id import SessionId

    return SessionExecution.restore(
        id=SessionExecutionId(model.id),
        user_execution_id=(
            UserExecutionId(model.user_execution_id) if model.user_execution_id else None
        ),
        session_id=SessionId(model.session_id) if model.session_id else None,
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def session_execution_entity_to_model(entity):
    return SessionExecutionModel(
        id=entity.id.value,
        user_execution_id=entity.user_execution_id.value if entity.user_execution_id else None,
        session_id=entity.session_id.value if entity.session_id else None,
        created_at=entity.created_at.value if entity.created_at else None,
    )


def session_execution_update_model(model: SessionExecutionModel, entity) -> None:
    model.user_execution_id = entity.user_execution_id.value if entity.user_execution_id else None
    model.session_id = entity.session_id.value if entity.session_id else None
    model.created_at = entity.created_at.value if entity.created_at else None


# ── SessionExecution State ─────────────────────────────────────────────────────


def session_execution_state_model_to_entity(model: SessionExecutionStateModel):
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


def session_execution_state_entity_to_model(entity):
    return SessionExecutionStateModel(
        id=entity.id.value,
        session_execution_id=entity.session_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        is_current=entity.is_current.value,
        created_at=entity.created_at.value if entity.created_at else None,
    )
