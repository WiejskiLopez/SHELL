"""SQL ORM model <-> domain entity mappers."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.entities.envelope import Envelope, EnvelopeEvent
from shell.domain.entities.graph_execution import GraphExecution
from shell.domain.entities.graph_definition import GraphDefinition
from shell.domain.entities.graph_node_definition import GraphNodeDefinition
from shell.domain.entities.graph_node_execution import GraphNodeExecution
from shell.domain.entities.graph_node_execution_result import GraphNodeExecutionResult
from shell.domain.entities.prompt import Prompt
from shell.domain.entities.runner_config import RunnerConfig
from shell.domain.entities.task_execution import TaskExecution
from shell.domain.entities.workflow import GraphNodeExecutionState, Workflow
from shell.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell.domain.value_objects.hash import Hash
from shell.domain.value_objects.ids import (
    EnvelopeEventId,
    EnvelopeId,
    GraphDefinitionId,
    GraphNodeDefinitionId,
    GraphExecutionId,
    GraphNodeExecutionId,
    GraphNodeExecutionResultId,
    GraphNodeExecutionStateId,
    PromptId,
    RunnerConfigId,
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.status import Status
from shell.domain.value_objects.task_execution_body import TaskExecutionBody
from shell.domain.value_objects.task_execution_name import TaskExecutionName
from shell.domain.value_objects.version import Version
from shell.infrastructure.persistence.sql.models import (
    EnvelopeEventModel,
    EnvelopeModel,
    GraphDefinitionModel,
    GraphNodeDefinitionModel,
    GraphExecutionModel,
    GraphNodeExecutionModel,
    GraphNodeExecutionResultModel,
    GraphNodeExecutionStateModel,
    PromptModel,
    RunnerConfigModel,
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
        version=Version(task_execution_model.version),
        hash=Hash(task_execution_model.hash),
        body=TaskExecutionBody(task_execution_model.body),
        is_current=task_execution_model.is_current,
        created_at=_ensure_utc(task_execution_model.created_at),
    )


def task_execution_entity_to_model(task_execution: TaskExecution) -> TaskExecutionModel:
    return TaskExecutionModel(
        id=task_execution.id.value,
        name=task_execution.name.value,
        version=task_execution.version.value,
        hash=task_execution.hash.value,
        body=task_execution.body.value,
        is_current=task_execution.is_current,
        created_at=task_execution.created_at,
    )


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


def graph_execution_model_to_entity(graph_execution_model: GraphExecutionModel) -> GraphExecution:
    graph_node_executions = [
        GraphNodeExecution(
            id=GraphNodeExecutionId(graph_node_execution_model.id),
            position=graph_node_execution_model.position,
            node_dir=graph_node_execution_model.node_dir,
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
            work_dir=graph_node_execution_model.work_dir,
            status_initial=graph_node_execution_model.status_initial,
            extra=dict(graph_node_execution_model.extra),
        )
        for graph_node_execution_model in graph_execution_model.graph_node_execution_models
    ]
    return GraphExecution(
        id=GraphExecutionId(graph_execution_model.id),
        task_execution_id=TaskExecutionId(graph_execution_model.task_execution_id),
        graph_definition_id=GraphDefinitionId(graph_execution_model.graph_definition_id),
        graph_node_executions=graph_node_executions,
    )


def graph_execution_entity_to_model(graph_execution: GraphExecution) -> GraphExecutionModel:
    graph_execution_model = GraphExecutionModel(
        id=graph_execution.id.value,
        task_execution_id=graph_execution.task_execution_id.value,
        graph_definition_id=str(graph_execution.graph_definition_id),
    )
    graph_execution_model.graph_node_execution_models = [
        GraphNodeExecutionModel(
            id=graph_node_execution.id.value,
            graph_execution_id=graph_execution.id.value,
            position=graph_node_execution.position,
            node_dir=graph_node_execution.node_dir,
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
            work_dir=graph_node_execution.work_dir,
            status_initial=graph_node_execution.status_initial,
            extra=graph_node_execution.extra,
        )
        for graph_node_execution in graph_execution.graph_node_executions
    ]
    return graph_execution_model


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


def workflow_model_to_entity(m: WorkflowModel) -> Workflow:
    graph_node_execution_states = {
        ns.graph_node_execution_id: GraphNodeExecutionState(
            id=GraphNodeExecutionStateId(ns.id),
            graph_node_execution_id=GraphNodeExecutionId(ns.graph_node_execution_id),
            status=Status(ns.status),
            step=ns.step,
            updated_at=_ensure_utc(ns.updated_at),
        )
        for ns in m.graph_node_execution_state_models
    }
    graph_node_execution_results = {nr.graph_node_execution_id: graph_node_execution_result_model_to_entity(nr) for nr in m.graph_node_execution_result_models}
    from shell.domain.value_objects.workflow_cursor import WorkflowCursor
    from shell.domain.value_objects.workflow_execution_context import (
        WorkflowExecutionContext,
    )

    cursor = (
        WorkflowCursor.at(GraphNodeExecutionId(m.current_graph_node_execution_id))
        if m.current_graph_node_execution_id
        else WorkflowCursor.empty()
    )
    context = WorkflowExecutionContext(
        work_dir=m.work_dir or "",
        correlation_id=m.correlation_id or "",
    )
    return Workflow(
        id=WorkflowId(m.id),
        task_execution_id=TaskExecutionId(m.task_execution_id),
        status=Status(m.status),
        created_at=_ensure_utc(m.created_at),
        cursor=cursor,
        execution_context=context,
        version=m.version,
        graph_node_execution_states=graph_node_execution_states,
        graph_node_execution_results=graph_node_execution_results,
    )


def workflow_entity_to_model(work_flow: Workflow) -> WorkflowModel:
    work_flow_model = WorkflowModel(
        id=work_flow.id.value,
        task_execution_id=work_flow.task_execution_id.value,
        status=work_flow.status.value,
        current_graph_node_execution_id=work_flow.cursor.current_graph_node_execution_id.value if work_flow.cursor.current_graph_node_execution_id else None,
        work_dir=work_flow.execution_context.work_dir,
        correlation_id=work_flow.execution_context.correlation_id,
        version=work_flow.version,
        created_at=work_flow.created_at,
    )
    # POPRAWKA: Zmiana nazwy na graph_node_execution_state_models
    work_flow_model.graph_node_execution_state_models = [
        GraphNodeExecutionStateModel(
            id=ns.id.value,
            workflow_id=work_flow.id.value,
            graph_node_execution_id=ns.graph_node_execution_id.value,
            status=ns.status.value,
            step=ns.step,
            updated_at=ns.updated_at,
        )
        for ns in work_flow.graph_node_execution_states.values()
    ]
    # POPRAWKA: Zmiana nazwy na graph_node_execution_result_models
    work_flow_model.graph_node_execution_result_models = [
        graph_node_execution_result_entity_to_model(nr)
        for nr in work_flow.graph_node_execution_results.values()
    ]
    return work_flow_model


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


def envelope_model_to_entity(m: EnvelopeModel) -> Envelope:
    evts = [
        EnvelopeEvent(
            id=EnvelopeEventId(e.id),
            kind=e.kind,
            payload=dict(e.payload),
            created_at=_ensure_utc(e.created_at),
        )
        for e in m.events
    ]
    return Envelope(
        id=EnvelopeId(m.id),
        workflow_id=WorkflowId(m.workflow_id),
        parent_id=EnvelopeId(m.parent_id) if m.parent_id else None,
        correlation_id=m.correlation_id,
        sender_graph_node_execution_id=GraphNodeExecutionId(m.sender_graph_node_execution_id),
        receiver_graph_node_execution_id=GraphNodeExecutionId(m.receiver_graph_node_execution_id),
        source_role=m.source_role,
        target_role=m.target_role,
        sequence_id=m.sequence_id,
        step=m.step,
        status=EnvelopeStatus(m.status),
        stage=EnvelopeStage(m.stage),
        payload=dict(m.payload),
        artifact_uri=m.artifact_uri,
        archive_uri=m.archive_uri,
        created_at=_ensure_utc(m.created_at),
        updated_at=_ensure_utc(m.updated_at),
        events=evts,
    )


def envelope_entity_to_model(e: Envelope) -> EnvelopeModel:
    m = EnvelopeModel(
        id=e.id.value,
        workflow_id=e.workflow_id.value,
        parent_id=e.parent_id.value if e.parent_id else None,
        correlation_id=e.correlation_id,
        sender_graph_node_execution_id=e.sender_graph_node_execution_id.value,
        receiver_graph_node_execution_id=e.receiver_graph_node_execution_id.value,
        source_role=e.source_role,
        target_role=e.target_role,
        sequence_id=e.sequence_id,
        step=e.step,
        status=e.status.value,
        stage=e.stage.value,
        payload=e.payload,
        artifact_uri=e.artifact_uri,
        archive_uri=e.archive_uri,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )
    m.events = [
        EnvelopeEventModel(
            id=ev.id.value,
            envelope_id=e.id.value,
            kind=ev.kind,
            payload=ev.payload,
            created_at=ev.created_at,
        )
        for ev in e.events
    ]
    return m


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------


def prompt_model_to_entity(m: PromptModel) -> Prompt:
    return Prompt(
        id=PromptId(m.id),
        name=m.name,
        version=m.version,
        hash=Hash(m.hash),
        body=m.body,
        source_uri=m.source_uri,
        is_current=m.is_current,
        created_at=_ensure_utc(m.created_at),
    )


def prompt_entity_to_model(p: Prompt) -> PromptModel:
    return PromptModel(
        id=p.id.value,
        name=p.name,
        version=p.version,
        hash=p.hash.value,
        body=p.body,
        source_uri=p.source_uri,
        is_current=p.is_current,
        created_at=p.created_at,
    )


# ---------------------------------------------------------------------------
# GraphNodeExecutionResult
# ---------------------------------------------------------------------------


def graph_node_execution_result_model_to_entity(m: GraphNodeExecutionResultModel) -> GraphNodeExecutionResult:
    return GraphNodeExecutionResult(
        id=GraphNodeExecutionResultId(m.id),
        graph_node_execution_id=GraphNodeExecutionId(m.graph_node_execution_id),
        workflow_id=WorkflowId(m.workflow_id),
        status=Status(m.status),
        stdout=m.stdout,
        stderr=m.stderr,
        artifact_uri=m.artifact_uri,
        created_at=_ensure_utc(m.created_at),
    )


def graph_node_execution_result_entity_to_model(graph_node_execution_result: GraphNodeExecutionResult) -> GraphNodeExecutionResultModel:
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


def runner_config_model_to_entity(m: RunnerConfigModel) -> RunnerConfig:
    return RunnerConfig(
        id=RunnerConfigId(m.id),
        package_name=m.package_name,
        kind=m.kind,
        hash=Hash(m.hash),
        body=dict(m.body),
        created_at=_ensure_utc(m.created_at),
    )


def runner_config_entity_to_model(c: RunnerConfig) -> RunnerConfigModel:
    return RunnerConfigModel(
        id=c.id.value,
        package_name=c.package_name,
        kind=c.kind,
        hash=c.hash.value,
        body=c.body,
        created_at=c.created_at,
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
        graph_node_definitions=[graph_node_definition_model_to_entity(node) for node in graph_definition_model.graph_node_execution_models],
    )


def graph_definition_entity_to_model(
    graph_definition: GraphDefinition,
) -> GraphDefinitionModel:
    m = GraphDefinitionModel(
        id=graph_definition.id,
        name=graph_definition.name,
        purpose=graph_definition.purpose,
    )
    m.graph_node_execution_models = [
        graph_node_definition_entity_to_model(
            node,
            graph_definition.id.value,
        )
        for node in graph_definition.graph_node_definitions
    ]
    return m


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
