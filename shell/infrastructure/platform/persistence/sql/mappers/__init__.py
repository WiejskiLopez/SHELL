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
from shell.domain.execution.aggregates.envelope import Envelope, EnvelopeEvent
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.value_objects.transition_definition import (
    TransitionDefinition,
)
from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_input import (
    GraphNodeExecutionStateInput,
)
from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_output import (
    GraphNodeExecutionStateOutput,
)
from shell.domain.execution.aggregates.session import Session
from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
    TaskExecutionState,
)
from shell.domain.execution.value_objects.state_kind import StateKind
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.aggregates.workflow.entities.graph_node_execution_result import (
    GraphNodeExecutionResult,
)
from shell.domain.execution.value_objects.ids import (
    EnvelopeEventId,
    EnvelopeId,
    GraphExecutionId,
    GraphExecutionStateId,
    GraphNodeExecutionId,
    GraphNodeExecutionResultId,
    GraphNodeExecutionStateInputId,
    GraphNodeExecutionStateOutputId,
    GraphNodeTransitionExecutionId,
    SessionId,
    TaskExecutionId,
    TaskExecutionStateId,
    WorkflowId,
)
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.execution.value_objects.work_dir import WorkDir
from shell.domain.platform.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell.domain.platform.value_objects.hash import Hash
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.platform.value_objects.status import Status
from shell.domain.execution.value_objects.edge_type import EdgeType
from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel,
    GraphNodeDefinitionModel,
    GraphNodeTransitionDefinitionModel,
    RagChunkModel,
    RagDocumentModel,
    RunnerConfigModel,
)
from shell.infrastructure.execution.persistence.sql.models import (
    EnvelopeEventModel,
    EnvelopeModel,
    GraphExecutionModel,
    GraphNodeExecutionResultModel,
    GraphNodeExecutionStateInputModel,
    GraphNodeExecutionStateOutputModel,
    GraphNodeTransitionExecutionModel,
    SessionModel,
    TaskExecutionModel,
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
# TaskExecution Input Payload
# ---------------------------------------------------------------------------


def task_execution_input_payload_model_to_entity(
    model: TaskExecutionStateInputModel,
) -> TaskExecutionState:
    return TaskExecutionState(
        id=TaskExecutionStateId(model.id),
        task_execution_id=TaskExecutionId(model.task_execution_id),
        kind=StateKind.INPUT,
        payload=dict(model.payload),
        is_current=model.is_current,
        created_at=_ensure_utc(model.created_at),
    )


def task_execution_input_payload_entity_to_model(
    entity: TaskExecutionState,
) -> TaskExecutionStateInputModel:
    return TaskExecutionStateInputModel(
        id=entity.id.value,
        task_execution_id=entity.task_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )


# ---------------------------------------------------------------------------
# TaskExecution Output Payload
# ---------------------------------------------------------------------------


def task_execution_output_payload_model_to_entity(
    model: TaskExecutionStateOutputModel,
) -> TaskExecutionState:
    return TaskExecutionState(
        id=TaskExecutionStateId(model.id),
        task_execution_id=TaskExecutionId(model.task_execution_id),
        kind=StateKind.OUTPUT,
        payload=dict(model.payload),
        is_current=model.is_current,
        created_at=_ensure_utc(model.created_at),
    )


def task_execution_output_payload_entity_to_model(
    entity: TaskExecutionState,
) -> TaskExecutionStateOutputModel:
    return TaskExecutionStateOutputModel(
        id=entity.id.value,
        task_execution_id=entity.task_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )


# ---------------------------------------------------------------------------
# GraphNodeExecution State Input
# ---------------------------------------------------------------------------


def graph_node_execution_state_input_model_to_entity(
    model: GraphNodeExecutionStateInputModel,
) -> GraphNodeExecutionStateInput:
    return GraphNodeExecutionStateInput(
        id=GraphNodeExecutionStateInputId(model.id),
        graph_node_execution_id=GraphNodeExecutionId(model.graph_node_execution_id),
        payload=dict(model.payload),
        is_current=model.is_current,
        created_at=_ensure_utc(model.created_at),
    )


def graph_node_execution_state_input_entity_to_model(
    entity: GraphNodeExecutionStateInput,
) -> GraphNodeExecutionStateInputModel:
    return GraphNodeExecutionStateInputModel(
        id=entity.id.value,
        graph_node_execution_id=entity.graph_node_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )


# ---------------------------------------------------------------------------
# GraphNodeExecution State Output
# ---------------------------------------------------------------------------


def graph_node_execution_state_output_model_to_entity(
    model: GraphNodeExecutionStateOutputModel,
) -> GraphNodeExecutionStateOutput:
    return GraphNodeExecutionStateOutput(
        id=GraphNodeExecutionStateOutputId(model.id),
        graph_node_execution_id=GraphNodeExecutionId(model.graph_node_execution_id),
        payload=dict(model.payload),
        is_current=model.is_current,
        created_at=_ensure_utc(model.created_at),
    )


def graph_node_execution_state_output_entity_to_model(
    entity: GraphNodeExecutionStateOutput,
) -> GraphNodeExecutionStateOutputModel:
    return GraphNodeExecutionStateOutputModel(
        id=entity.id.value,
        graph_node_execution_id=entity.graph_node_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
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
        depth=graph_execution_model.depth,
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
    model.parent_graph_execution_id = entity.parent_graph_execution_id.value if entity.parent_graph_execution_id else None
    model.depth = entity.depth.value if hasattr(entity.depth, 'value') else entity.depth


def graph_execution_entity_to_model(
    graph_execution: GraphExecution,
) -> GraphExecutionModel:
    graph_execution_model = GraphExecutionModel(
        id=graph_execution.id.value,
        task_execution_id=graph_execution.task_execution_id.value,
        graph_definition_id="",
        parent_graph_execution_id=(
            graph_execution.parent_graph_execution_id.value
            if graph_execution.parent_graph_execution_id
            else None
        ),
        state_input={},
        state_output={},
        depth=graph_execution.depth.value if graph_execution.depth else 0,
        timeout_at=None,
        correlation_id="",
        tags={},
    )
    return graph_execution_model


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


def workflow_model_to_entity(workflow_model: WorkflowModel) -> Workflow:
    return Workflow(
        id=WorkflowId(workflow_model.id),
        status=Status(workflow_model.status),
        session_id=SessionId(workflow_model.session_id) if workflow_model.session_id else None,
        created_at=_ensure_utc(workflow_model.created_at),
    )


def workflow_entity_to_model(work_flow: Workflow) -> WorkflowModel:
    return WorkflowModel(
        id=work_flow.id.value,
        status=work_flow.status.value,
        session_id=work_flow.session_id.value if work_flow.session_id else None,
        created_at=work_flow.created_at,
    )


def workflow_update_model(model: WorkflowModel, entity: Workflow) -> None:
    model.status = entity.status.value if hasattr(entity.status, 'value') else entity.status
    model.session_id = entity.session_id.value if entity.session_id else None
    model.created_at = entity.created_at


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


def envelope_model_to_entity(envelope_model: EnvelopeModel) -> Envelope:
    events = [
        EnvelopeEvent(
            id=EnvelopeEventId(event_model.id),
            kind=event_model.kind,
            payload=dict(event_model.payload),
            created_at=_ensure_utc(event_model.created_at),
        )
        for event_model in envelope_model.events
    ]
    from shell.domain.execution.aggregates.envelope.value_objects.archive_uri import ArchiveUri
    from shell.domain.execution.aggregates.envelope.value_objects.artifact_uri import ArtifactUri
    from shell.domain.execution.aggregates.envelope.value_objects.correlation_id import CorrelationId
    from shell.domain.execution.aggregates.envelope.value_objects.payload import Payload
    from shell.domain.execution.aggregates.envelope.value_objects.sequence_id import SequenceId
    from shell.domain.execution.aggregates.envelope.value_objects.source_role import SourceRole
    from shell.domain.execution.aggregates.envelope.value_objects.step import Step
    from shell.domain.execution.aggregates.envelope.value_objects.target_role import TargetRole
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.platform.value_objects.updated_at import UpdatedAt

    return Envelope(
        id=EnvelopeId(envelope_model.id),
        workflow_id=WorkflowId(envelope_model.workflow_id),
        parent_id=EnvelopeId(envelope_model.parent_id) if envelope_model.parent_id else None,
        correlation_id=CorrelationId(envelope_model.correlation_id),
        sender_graph_node_execution_id=GraphNodeExecutionId(
            envelope_model.sender_graph_node_execution_id
        ),
        receiver_graph_node_execution_id=GraphNodeExecutionId(
            envelope_model.receiver_graph_node_execution_id
        ),
        source_role=SourceRole(envelope_model.source_role),
        target_role=TargetRole(envelope_model.target_role),
        sequence_id=SequenceId(envelope_model.sequence_id),
        step=Step(envelope_model.step),
        status=EnvelopeStatus(envelope_model.status),
        stage=EnvelopeStage(envelope_model.stage),
        payload=Payload(dict(envelope_model.payload)),
        artifact_uri=ArtifactUri(envelope_model.artifact_uri),
        archive_uri=ArchiveUri(envelope_model.archive_uri),
        created_at=CreatedAt.from_datetime(_ensure_utc(envelope_model.created_at)),
        updated_at=UpdatedAt.from_datetime(_ensure_utc(envelope_model.updated_at)),
        events=events,
    )


def envelope_entity_to_model(envelope: Envelope) -> EnvelopeModel:
    envelope_model = EnvelopeModel(
        id=envelope.id.value,
        workflow_id=envelope.workflow_id.value,
        parent_id=envelope.parent_id.value if envelope.parent_id else None,
        correlation_id=envelope.correlation_id.value,
        sender_graph_node_execution_id=envelope.sender_graph_node_execution_id.value,
        receiver_graph_node_execution_id=envelope.receiver_graph_node_execution_id.value,
        source_role=envelope.source_role.value,
        target_role=envelope.target_role.value,
        sequence_id=envelope.sequence_id.value,
        step=envelope.step.value,
        status=envelope.status.value,
        stage=envelope.stage.value,
        payload=envelope.payload.value,
        artifact_uri=envelope.artifact_uri.value,
        archive_uri=envelope.archive_uri.value,
        created_at=envelope.created_at.value,
        updated_at=envelope.updated_at.value,
    )
    envelope_model.events = [
        EnvelopeEventModel(
            id=envelope_event.id.value,
            envelope_id=envelope.id.value,
            kind=envelope_event.kind,
            payload=envelope_event.payload,
            created_at=envelope_event.created_at,
        )
        for envelope_event in envelope.events
    ]
    return envelope_model


def envelope_update_model(model: EnvelopeModel, entity: Envelope) -> None:
    model.workflow_id = entity.workflow_id.value
    model.parent_id = entity.parent_id.value if entity.parent_id else None
    model.correlation_id = entity.correlation_id.value
    model.sender_graph_node_execution_id = entity.sender_graph_node_execution_id.value
    model.receiver_graph_node_execution_id = entity.receiver_graph_node_execution_id.value
    model.source_role = entity.source_role.value
    model.target_role = entity.target_role.value
    model.sequence_id = entity.sequence_id.value
    model.step = entity.step.value
    model.status = entity.status.value
    model.stage = entity.stage.value
    model.payload = entity.payload.value
    model.artifact_uri = entity.artifact_uri.value
    model.archive_uri = entity.archive_uri.value
    model.created_at = entity.created_at.value
    model.updated_at = entity.updated_at.value
    # Events are managed separately via add/remove on the relationship


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
    return Session(
        id=SessionId(session_model.id),
        goal=session_model.goal,
        status=session_model.status,
        opened_at=_ensure_utc(session_model.opened_at),
        closed_at=_ensure_utc(session_model.closed_at) if session_model.closed_at else None,
    )


def session_entity_to_model(session: Session) -> SessionModel:
    return SessionModel(
        id=session.id.value,
        goal=session.goal,
        status=session.status,
        opened_at=session.opened_at,
        closed_at=session.closed_at,
    )


def session_update_model(model: SessionModel, entity: Session) -> None:
    model.goal = entity.goal
    model.status = entity.status
    model.opened_at = entity.opened_at
    model.closed_at = entity.closed_at


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
    from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.value_objects.state_kind import StateKind

    return GraphExecutionState(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        kind=StateKind.INPUT,
        state_data=dict(model.payload) if model.payload else {},
        is_current=model.is_current,
        created_at=model.created_at,
    )


def graph_execution_state_input_entity_to_model(entity):
    from shell.infrastructure.execution.persistence.sql.models.graph_execution_state_input import (
        GraphExecutionStateInputModel,
    )

    return GraphExecutionStateInputModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        payload=entity.state_data,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )


# ── GraphExecutionStateOutput ─────────────────────────────────────────────────


def graph_execution_state_output_model_to_entity(model):
    from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )
    from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
        GraphExecutionStateId,
    )
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.value_objects.state_kind import StateKind

    return GraphExecutionState(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        kind=StateKind.OUTPUT,
        state_data=dict(model.payload) if model.payload else {},
        is_current=model.is_current,
        created_at=model.created_at,
    )


def graph_execution_state_output_entity_to_model(entity):
    from shell.infrastructure.execution.persistence.sql.models.graph_execution_state_output import (
        GraphExecutionStateOutputModel,
    )

    return GraphExecutionStateOutputModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        payload=entity.state_data,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )
