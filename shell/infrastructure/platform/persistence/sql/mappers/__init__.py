"""SQL ORM model <-> domain entity mappers."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.entities.envelope import Envelope, EnvelopeEvent
from shell.domain.definition.entities.graph_definition import GraphDefinition
from shell.domain.definition.entities.rag_document import RagChunk, RagDocument
from shell.domain.execution.entities.session import Message, Session
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_node_execution_input_payload import (
    GraphNodeExecutionInputPayload,
)
from shell.domain.execution.aggregates.graph_node_execution_output_payload import (
    GraphNodeExecutionOutputPayload,
)
from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
from shell.domain.execution.entities.graph_node_execution import GraphNodeExecution
from shell.domain.execution.entities.graph_node_execution_result import GraphNodeExecutionResult
from shell.domain.execution.entities.graph_node_transition_execution import GraphNodeTransitionExecution
from shell.domain.definition.entities.graph_node_transition_definition import GraphNodeTransitionDefinition
from shell.domain.definition.entities.prompt import Prompt
from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.execution.aggregates.task_execution import TaskExecution
from shell.domain.execution.aggregates.task_execution_input_payload import (
    TaskExecutionInputPayload,
)
from shell.domain.execution.aggregates.task_execution_output_payload import (
    TaskExecutionOutputPayload,
)
from shell.domain.execution.aggregates.workflow import GraphNodeExecutionState, Workflow
from shell.domain.platform.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell.domain.platform.value_objects.hash import Hash
from shell.domain.platform.value_objects.ids import (
    CorrelationId
)
from shell.domain.definition.value_objects.ids import (
    GraphDefinitionId,
    GraphNodeDefinitionId,
    GraphNodeTransitionDefinitionId,
    PromptId,
    RagChunkId,
    RagDocumentId,
    RunnerConfigId
)
from shell.domain.execution.value_objects.ids import (
    EnvelopeEventId,
    EnvelopeId,
    GraphExecutionId,
    GraphNodeExecutionId,
    GraphNodeExecutionInputPayloadId,
    GraphNodeTransitionExecutionId,
    GraphNodeExecutionOutputPayloadId,
    GraphNodeExecutionResultId,
    GraphNodeExecutionStateId,
    MessageId,
    SessionId,
    TaskExecutionId,
    TaskExecutionInputPayloadId,
    TaskExecutionOutputPayloadId,
    WorkflowId
)
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.platform.value_objects.status import Status
from shell.domain.execution.value_objects.task_execution_body import TaskExecutionBody
from shell.domain.platform.value_objects.transition_type import TransitionType
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.value_objects.version import Version
from shell.infrastructure.platform.persistence.sql.models import (
    MessageModel
)
from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel,
    GraphNodeDefinitionModel,
    GraphNodeTransitionDefinitionModel,
    PromptModel,
    RagChunkModel,
    RagDocumentModel,
    RunnerConfigModel
)
from shell.infrastructure.execution.persistence.sql.models import (
    EnvelopeEventModel,
    EnvelopeModel,
    GraphExecutionModel,
    GraphNodeExecutionInputPayloadModel,
    GraphNodeExecutionModel,
    GraphNodeExecutionOutputPayloadModel,
    GraphNodeExecutionResultModel,
    GraphNodeExecutionStateModel,
    GraphNodeTransitionExecutionModel,
    SessionModel,
    TaskExecutionInputPayloadModel,
    TaskExecutionModel,
    TaskExecutionOutputPayloadModel,
    WorkflowModel
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
        parent_task_execution_id=(
            TaskExecutionId(task_execution_model.parent_task_execution_id)
            if task_execution_model.parent_task_execution_id
            else None
        ),
        name=TaskExecutionName(task_execution_model.name),
        version=Version(task_execution_model.version),
        hash=Hash(task_execution_model.hash),
        body=TaskExecutionBody(task_execution_model.body),
        is_current=task_execution_model.is_current,
        created_at=_ensure_utc(task_execution_model.created_at),
        work_dir=task_execution_model.work_dir or "",
    )


def task_execution_entity_to_model(task_execution: TaskExecution) -> TaskExecutionModel:
    return TaskExecutionModel(
        id=task_execution.id.value,
        parent_task_execution_id=(
            task_execution.parent_task_execution_id.value
            if task_execution.parent_task_execution_id
            else None
        ),
        name=task_execution.name.value,
        version=task_execution.version.value,
        hash=task_execution.hash.value,
        body=task_execution.body.value,
        is_current=task_execution.is_current,
        work_dir=task_execution.work_dir,
        created_at=task_execution.created_at,
    )


# ---------------------------------------------------------------------------
# TaskExecution Input Payload
# ---------------------------------------------------------------------------


def task_execution_input_payload_model_to_entity(
    model: TaskExecutionInputPayloadModel,
) -> TaskExecutionInputPayload:
    return TaskExecutionInputPayload(
        id=TaskExecutionInputPayloadId(model.id),
        task_execution_id=TaskExecutionId(model.task_execution_id),
        payload=dict(model.payload),
        is_current=model.is_current,
        created_at=_ensure_utc(model.created_at),
    )


def task_execution_input_payload_entity_to_model(
    entity: TaskExecutionInputPayload,
) -> TaskExecutionInputPayloadModel:
    return TaskExecutionInputPayloadModel(
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
    model: TaskExecutionOutputPayloadModel,
) -> TaskExecutionOutputPayload:
    return TaskExecutionOutputPayload(
        id=TaskExecutionOutputPayloadId(model.id),
        task_execution_id=TaskExecutionId(model.task_execution_id),
        payload=dict(model.payload),
        is_current=model.is_current,
        created_at=_ensure_utc(model.created_at),
    )


def task_execution_output_payload_entity_to_model(
    entity: TaskExecutionOutputPayload,
) -> TaskExecutionOutputPayloadModel:
    return TaskExecutionOutputPayloadModel(
        id=entity.id.value,
        task_execution_id=entity.task_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )


# ---------------------------------------------------------------------------
# GraphNodeExecution Input Payload
# ---------------------------------------------------------------------------


def graph_node_execution_input_payload_model_to_entity(
    model: GraphNodeExecutionInputPayloadModel,
) -> GraphNodeExecutionInputPayload:
    return GraphNodeExecutionInputPayload(
        id=GraphNodeExecutionInputPayloadId(model.id),
        graph_node_execution_id=GraphNodeExecutionId(model.graph_node_execution_id),
        payload=dict(model.payload),
        is_current=model.is_current,
        created_at=_ensure_utc(model.created_at),
    )


def graph_node_execution_input_payload_entity_to_model(
    entity: GraphNodeExecutionInputPayload,
) -> GraphNodeExecutionInputPayloadModel:
    return GraphNodeExecutionInputPayloadModel(
        id=entity.id.value,
        graph_node_execution_id=entity.graph_node_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )


# ---------------------------------------------------------------------------
# GraphNodeExecution Output Payload
# ---------------------------------------------------------------------------


def graph_node_execution_output_payload_model_to_entity(
    model: GraphNodeExecutionOutputPayloadModel,
) -> GraphNodeExecutionOutputPayload:
    return GraphNodeExecutionOutputPayload(
        id=GraphNodeExecutionOutputPayloadId(model.id),
        graph_node_execution_id=GraphNodeExecutionId(model.graph_node_execution_id),
        payload=dict(model.payload),
        is_current=model.is_current,
        created_at=_ensure_utc(model.created_at),
    )


def graph_node_execution_output_payload_entity_to_model(
    entity: GraphNodeExecutionOutputPayload,
) -> GraphNodeExecutionOutputPayloadModel:
    return GraphNodeExecutionOutputPayloadModel(
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
    graph_node_executions = [
        GraphNodeExecution(
            id=GraphNodeExecutionId(graph_node_execution_model.id),
            position=graph_node_execution_model.position,
            mode=Mode(graph_node_execution_model.mode),
            role=graph_node_execution_model.role,
            node_type=graph_node_execution_model.node_type,
            model=graph_node_execution_model.model,
            command=graph_node_execution_model.command,
            timeout=graph_node_execution_model.timeout,
            retries=graph_node_execution_model.retries,
            log_level=graph_node_execution_model.log_level,
            max_step=graph_node_execution_model.max_step,
            no_ask_user=graph_node_execution_model.no_ask_user,
            autopilot=graph_node_execution_model.autopilot,
            task_execution_id=graph_node_execution_model.task_execution_id,
            source_dir=graph_node_execution_model.source_dir,
            status_initial=graph_node_execution_model.status_initial,
            sub_graph_definition_id=graph_node_execution_model.sub_graph_definition_id,
            sub_graph_definition_version=graph_node_execution_model.sub_graph_definition_version,
            timeout_seconds=graph_node_execution_model.timeout_seconds,
            max_retries=graph_node_execution_model.max_retries,
            retry_delay_seconds=graph_node_execution_model.retry_delay_seconds,
            extra=dict(graph_node_execution_model.extra),
        )
        for graph_node_execution_model in graph_execution_model.graph_node_execution_models
    ]
    transitions = [
        graph_node_transition_execution_model_to_entity(t)
        for t in graph_execution_model.graph_node_transition_execution_models
    ]
    return GraphExecution(
        id=GraphExecutionId(graph_execution_model.id),
        task_execution_id=TaskExecutionId(graph_execution_model.task_execution_id),
        graph_definition_id=GraphDefinitionId(graph_execution_model.graph_definition_id),
        graph_node_executions=graph_node_executions,
        transitions=transitions,
        parent_graph_execution_id=(
            GraphExecutionId(graph_execution_model.parent_graph_execution_id)
            if graph_execution_model.parent_graph_execution_id
            else None
        ),
        parent_tasker_node_execution_id=(
            GraphNodeExecutionId(graph_execution_model.parent_tasker_node_execution_id)
            if graph_execution_model.parent_tasker_node_execution_id
            else None
        ),
        state_input=dict(graph_execution_model.state_input),
        state_output=dict(graph_execution_model.state_output),
        depth=graph_execution_model.depth,
        timeout_at=graph_execution_model.timeout_at,
        correlation_id=graph_execution_model.correlation_id or "",
        tags=dict(graph_execution_model.tags),
    )


def graph_node_transition_execution_model_to_entity(
    model: GraphNodeTransitionExecutionModel,
) -> GraphNodeTransitionExecution:
    return GraphNodeTransitionExecution(
        id=GraphNodeTransitionExecutionId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        source_node_execution_id=(
            GraphNodeExecutionId(model.source_node_execution_id)
            if model.source_node_execution_id
            else None
        ),
        target_node_execution_id=GraphNodeExecutionId(model.target_node_execution_id),
        transition_type=TransitionType(model.transition_type),
        priority=model.priority,
        condition_expression=model.condition_expression,
        condition_language=model.condition_language,
        join_wait_count=model.join_wait_count,
        max_loop_count=model.max_loop_count,
        timeout_seconds=model.timeout_seconds,
        retry_count=model.retry_count,
        retry_delay_seconds=model.retry_delay_seconds,
        data_mapping=dict(model.data_mapping) if model.data_mapping else None,
        label=model.label,
    )


def graph_node_transition_execution_entity_to_model(
    transition: GraphNodeTransitionExecution,
    now: datetime,
) -> GraphNodeTransitionExecutionModel:
    return GraphNodeTransitionExecutionModel(
        id=transition.id.value,
        graph_execution_id=transition.graph_execution_id.value,
        source_node_execution_id=(
            transition.source_node_execution_id.value
            if transition.source_node_execution_id
            else None
        ),
        target_node_execution_id=transition.target_node_execution_id.value,
        transition_type=transition.transition_type.value,
        priority=transition.priority,
        condition_expression=transition.condition_expression,
        condition_language=transition.condition_language,
        join_wait_count=transition.join_wait_count,
        max_loop_count=transition.max_loop_count,
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
        transition_type=TransitionType(model.transition_type),
        priority=model.priority,
        condition_expression=model.condition_expression,
        condition_language=model.condition_language,
        join_wait_count=model.join_wait_count,
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
        join_wait_count=transition.join_wait_count,
        max_loop_count=transition.max_loop_count,
        timeout_seconds=transition.timeout_seconds,
        retry_count=transition.retry_count,
        retry_delay_seconds=transition.retry_delay_seconds,
        data_mapping=transition.data_mapping,
        label=transition.label,
        created_at=now,
        updated_at=now,
    )


def graph_execution_entity_to_model(
    graph_execution: GraphExecution,
) -> GraphExecutionModel:
    graph_execution_model = GraphExecutionModel(
        id=graph_execution.id.value,
        task_execution_id=graph_execution.task_execution_id.value,
        graph_definition_id=str(graph_execution.graph_definition_id),
        parent_graph_execution_id=(
            graph_execution.parent_graph_execution_id.value
            if graph_execution.parent_graph_execution_id
            else None
        ),
        parent_tasker_node_execution_id=(
            graph_execution.parent_tasker_node_execution_id.value
            if graph_execution.parent_tasker_node_execution_id
            else None
        ),
        state_input=graph_execution.state_input,
        state_output=graph_execution.state_output,
        depth=graph_execution.depth,
        timeout_at=graph_execution.timeout_at,
        correlation_id=graph_execution.correlation_id,
        tags=graph_execution.tags,
    )
    graph_execution_model.graph_node_execution_models = [
        GraphNodeExecutionModel(
            id=graph_node_execution.id.value,
            graph_execution_id=graph_execution.id.value,
            position=graph_node_execution.position,
            mode=graph_node_execution.mode.value,
            role=graph_node_execution.role,
            node_type=graph_node_execution.node_type,
            model=graph_node_execution.model,
            command=graph_node_execution.command,
            timeout=graph_node_execution.timeout,
            retries=graph_node_execution.retries,
            log_level=graph_node_execution.log_level,
            max_step=graph_node_execution.max_step,
            no_ask_user=graph_node_execution.no_ask_user,
            autopilot=graph_node_execution.autopilot,
            task_execution_id=graph_node_execution.task_execution_id,
            source_dir=graph_node_execution.source_dir,
            status_initial=graph_node_execution.status_initial,
            sub_graph_definition_id=graph_node_execution.sub_graph_definition_id,
            sub_graph_definition_version=graph_node_execution.sub_graph_definition_version,
            timeout_seconds=graph_node_execution.timeout_seconds,
            max_retries=graph_node_execution.max_retries,
            retry_delay_seconds=graph_node_execution.retry_delay_seconds,
            extra=graph_node_execution.extra,
        )
        for graph_node_execution in graph_execution.graph_node_executions
    ]
    _now = datetime.now(UTC)
    graph_execution_model.graph_node_transition_execution_models = [
        graph_node_transition_execution_entity_to_model(t, _now)
        for t in graph_execution.transitions
    ]
    return graph_execution_model


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


def workflow_model_to_entity(workflow_model: WorkflowModel) -> Workflow:
    graph_node_execution_states = {
        state_model.graph_node_execution_id: GraphNodeExecutionState(
            id=GraphNodeExecutionStateId(state_model.id),
            graph_node_execution_id=GraphNodeExecutionId(state_model.graph_node_execution_id),
            status=Status(state_model.status),
            step=state_model.step,
            updated_at=_ensure_utc(state_model.updated_at),
        )
        for state_model in workflow_model.graph_node_execution_state_models
    }
    graph_node_execution_results = {
        result_model.graph_node_execution_id: graph_node_execution_result_model_to_entity(result_model)
        for result_model in workflow_model.graph_node_execution_result_models
    }
    from shell.domain.execution.value_objects.workflow_cursor import WorkflowCursor
    from shell.domain.execution.value_objects.workflow_execution_context import (
        WorkflowExecutionContext,
    )

    cursor = (
        WorkflowCursor.at(GraphNodeExecutionId(workflow_model.current_graph_node_execution_id))
        if workflow_model.current_graph_node_execution_id
        else WorkflowCursor.empty()
    )
    context = WorkflowExecutionContext(
        correlation_id=workflow_model.correlation_id or "",
    )
    return Workflow(
        id=WorkflowId(workflow_model.id),
        task_execution_id=TaskExecutionId(workflow_model.task_execution_id),
        status=Status(workflow_model.status),
        created_at=_ensure_utc(workflow_model.created_at),
        cursor=cursor,
        execution_context=context,
        version=workflow_model.version,
        graph_node_execution_states=graph_node_execution_states,
        graph_node_execution_results=graph_node_execution_results,
    )


def workflow_entity_to_model(work_flow: Workflow) -> WorkflowModel:
    work_flow_model = WorkflowModel(
        id=work_flow.id.value,
        task_execution_id=work_flow.task_execution_id.value,
        status=work_flow.status.value,
        current_graph_node_execution_id=work_flow.cursor.current_graph_node_execution_id.value
        if work_flow.cursor.current_graph_node_execution_id
        else None,
        correlation_id=work_flow.execution_context.correlation_id,
        version=work_flow.version,
        created_at=work_flow.created_at,
    )
    # POPRAWKA: Zmiana nazwy na graph_node_execution_state_models
    work_flow_model.graph_node_execution_state_models = [
        GraphNodeExecutionStateModel(
            id=node_state.id.value,
            workflow_id=work_flow.id.value,
            graph_node_execution_id=node_state.graph_node_execution_id.value,
            status=node_state.status.value,
            step=node_state.step,
            updated_at=node_state.updated_at,
        )
        for node_state in work_flow.graph_node_execution_states
    ]
    work_flow_model.graph_node_execution_result_models = [
        graph_node_execution_result_entity_to_model(node_result)
        for node_result in work_flow.graph_node_execution_results
    ]
    return work_flow_model


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
    return Envelope(
        id=EnvelopeId(envelope_model.id),
        workflow_id=WorkflowId(envelope_model.workflow_id),
        parent_id=EnvelopeId(envelope_model.parent_id) if envelope_model.parent_id else None,
        correlation_id=envelope_model.correlation_id,
        sender_graph_node_execution_id=GraphNodeExecutionId(envelope_model.sender_graph_node_execution_id),
        receiver_graph_node_execution_id=GraphNodeExecutionId(envelope_model.receiver_graph_node_execution_id),
        source_role=envelope_model.source_role,
        target_role=envelope_model.target_role,
        sequence_id=envelope_model.sequence_id,
        step=envelope_model.step,
        status=EnvelopeStatus(envelope_model.status),
        stage=EnvelopeStage(envelope_model.stage),
        payload=dict(envelope_model.payload),
        artifact_uri=envelope_model.artifact_uri,
        archive_uri=envelope_model.archive_uri,
        created_at=_ensure_utc(envelope_model.created_at),
        updated_at=_ensure_utc(envelope_model.updated_at),
        events=events,
    )


def envelope_entity_to_model(envelope: Envelope) -> EnvelopeModel:
    envelope_model = EnvelopeModel(
        id=envelope.id.value,
        workflow_id=envelope.workflow_id.value,
        parent_id=envelope.parent_id.value if envelope.parent_id else None,
        correlation_id=envelope.correlation_id,
        sender_graph_node_execution_id=envelope.sender_graph_node_execution_id.value,
        receiver_graph_node_execution_id=envelope.receiver_graph_node_execution_id.value,
        source_role=envelope.source_role,
        target_role=envelope.target_role,
        sequence_id=envelope.sequence_id,
        step=envelope.step,
        status=envelope.status.value,
        stage=envelope.stage.value,
        payload=envelope.payload,
        artifact_uri=envelope.artifact_uri,
        archive_uri=envelope.archive_uri,
        created_at=envelope.created_at,
        updated_at=envelope.updated_at,
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


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------


def prompt_model_to_entity(prompt_model: PromptModel) -> Prompt:
    return Prompt(
        id=PromptId(prompt_model.id),
        name=prompt_model.name,
        version=prompt_model.version,
        hash=Hash(prompt_model.hash),
        body=prompt_model.body,
        source_uri=prompt_model.source_uri,
        is_current=prompt_model.is_current,
        created_at=_ensure_utc(prompt_model.created_at),
    )


def prompt_entity_to_model(prompt: Prompt) -> PromptModel:
    return PromptModel(
        id=prompt.id.value,
        name=prompt.name,
        version=prompt.version,
        hash=prompt.hash.value,
        body=prompt.body,
        source_uri=prompt.source_uri,
        is_current=prompt.is_current,
        created_at=prompt.created_at,
    )


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
        extra=dict(graph_node_definition_model.extra or {}),
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
        extra=graph_node_definition.extra,
        script=graph_node_definition.script,
        script_type=graph_node_definition.script_type,
    )


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
        messages=[message_model_to_entity(m) for m in session_model.messages],
    )


def session_entity_to_model(session: Session) -> SessionModel:
    model = SessionModel(
        id=session.id.value,
        goal=session.goal,
        status=session.status,
        opened_at=session.opened_at,
        closed_at=session.closed_at,
    )
    model.messages = [message_entity_to_model(m) for m in session.messages]
    return model


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------


def message_model_to_entity(message_model: MessageModel) -> Message:
    return Message(
        id=MessageId(message_model.id),
        session_id=SessionId(message_model.session_id),
        correlation_id=CorrelationId(message_model.correlation_id),
        sender=message_model.sender,
        receiver=message_model.receiver,
        payload=dict(message_model.payload),
        created_at=_ensure_utc(message_model.created_at),
    )


def message_entity_to_model(message: Message) -> MessageModel:
    return MessageModel(
        id=message.id.value,
        session_id=message.session_id.value,
        correlation_id=message.correlation_id.value,
        sender=message.sender,
        receiver=message.receiver,
        payload=message.payload,
        created_at=message.created_at,
    )


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


# ── GraphExecutionState ──────────────────────────────────────────────────────


def graph_execution_state_model_to_entity(model):
    from shell.domain.execution.aggregates.graph_execution.graph_execution_state import (
        GraphExecutionState,
    )
    from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphExecutionStateId

    return GraphExecutionState(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        state_data=dict(model.payload) if model.payload else {},
        is_current=model.is_current,
        created_at=model.created_at,
    )


def graph_execution_state_entity_to_model(entity):
    from shell.infrastructure.execution.persistence.sql.models.graph_execution_state import (
        GraphExecutionStateModel,
    )

    return GraphExecutionStateModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        payload=entity.state_data,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )
