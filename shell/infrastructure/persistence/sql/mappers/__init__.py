"""SQL ORM model <-> domain entity mappers."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.entities.envelope import Envelope, EnvelopeEvent
from shell.domain.entities.graph import Graph
from shell.domain.entities.graph_definition import GraphDefinition
from shell.domain.entities.graph_definition_node import GraphDefinitionNode
from shell.domain.entities.graph_node import GraphNode
from shell.domain.entities.node_result import NodeResult
from shell.domain.entities.prompt import Prompt
from shell.domain.entities.runner_config import RunnerConfig
from shell.domain.entities.task_execution import TaskExecution
from shell.domain.entities.workflow import NodeState, Workflow
from shell.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell.domain.value_objects.hash import Hash
from shell.domain.value_objects.ids import (
    EnvelopeEventId,
    EnvelopeId,
    GraphDefinitionId,
    GraphDefinitionNodeId,
    GraphId,
    NodeId,
    NodeResultId,
    NodeStateId,
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
    GraphDefinitionNodeModel,
    GraphModel,
    GraphNodeModel,
    NodeResultModel,
    NodeStateModel,
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


def task_model_to_entity(m: TaskExecutionModel) -> TaskExecution:
    return TaskExecution(
        id=TaskExecutionId(m.id),
        name=TaskExecutionName(m.name),
        version=Version(m.version),
        hash=Hash(m.hash),
        body=TaskExecutionBody(m.body),
        is_current=m.is_current,
        created_at=_ensure_utc(m.created_at),
    )


def task_entity_to_model(task_execution: TaskExecution) -> TaskExecutionModel:
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


def graph_model_to_entity(m: GraphModel) -> Graph:
    nodes = [
        GraphNode(
            id=NodeId(n.id),
            position=n.position,
            node_dir=n.node_dir,
            mode=Mode(n.mode),
            role=n.role,
            node_type=n.node_type,
            model=n.model,
            command=n.command,
            timeout=n.timeout,
            retries=n.retries,
            log_level=n.log_level,
            max_step=n.max_step,
            no_ask_user=n.no_ask_user,
            autopilot=n.autopilot,
            task_execution_id=n.task_execution_id,
            source_dir=n.source_dir,
            work_dir=n.work_dir,
            status_initial=n.status_initial,
            extra=dict(n.extra),
        )
        for n in m.nodes
    ]
    return Graph(
        id=GraphId(m.id),
        task_execution_id=TaskExecutionId(m.task_execution_id),
        graph_definition_id=GraphDefinitionId(m.graph_definition_id),
        nodes=nodes,
    )


def graph_entity_to_model(graph: Graph) -> GraphModel:
    m = GraphModel(
        id=graph.id.value,
        task_execution_id=graph.task_execution_id.value,
        graph_definition_id=str(graph.graph_definition_id),
    )
    m.nodes = [
        GraphNodeModel(
            id=n.id.value,
            graph_id=graph.id.value,
            position=n.position,
            node_dir=n.node_dir,
            mode=n.mode.value,
            role=n.role,
            node_type=n.node_type,
            model=n.model,
            command=n.command,
            timeout=n.timeout,
            retries=n.retries,
            log_level=n.log_level,
            max_step=n.max_step,
            no_ask_user=n.no_ask_user,
            autopilot=n.autopilot,
            task_execution_id=n.task_execution_id,
            source_dir=n.source_dir,
            work_dir=n.work_dir,
            status_initial=n.status_initial,
            extra=n.extra,
        )
        for n in graph.nodes
    ]
    return m


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


def workflow_model_to_entity(m: WorkflowModel) -> Workflow:
    states = {
        ns.node_id: NodeState(
            id=NodeStateId(ns.id),
            node_id=NodeId(ns.node_id),
            status=Status(ns.status),
            step=ns.step,
            updated_at=_ensure_utc(ns.updated_at),
        )
        for ns in m.node_states
    }
    results = {nr.node_id: node_result_model_to_entity(nr) for nr in m.node_results}
    from shell.domain.value_objects.workflow_cursor import WorkflowCursor
    from shell.domain.value_objects.workflow_execution_context import (
        WorkflowExecutionContext,
    )

    cursor = (
        WorkflowCursor.at(NodeId(m.current_node_id))
        if m.current_node_id
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
        node_states=states,
        node_results=results,
    )


def workflow_entity_to_model(w: Workflow) -> WorkflowModel:
    m = WorkflowModel(
        id=w.id.value,
        task_execution_id=w.task_execution_id.value,
        status=w.status.value,
        current_node_id=w.cursor.current_node_id.value if w.cursor.current_node_id else None,
        work_dir=w.execution_context.work_dir,
        correlation_id=w.execution_context.correlation_id,
        version=w.version,
        created_at=w.created_at,
    )
    m.node_states = [
        NodeStateModel(
            id=ns.id.value,
            workflow_id=w.id.value,
            node_id=ns.node_id.value,
            status=ns.status.value,
            step=ns.step,
            updated_at=ns.updated_at,
        )
        for ns in w.node_states.values()
    ]
    m.node_results = [node_result_entity_to_model(nr) for nr in w.node_results.values()]
    return m


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
        sender_node_id=NodeId(m.sender_node_id),
        receiver_node_id=NodeId(m.receiver_node_id),
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
        sender_node_id=e.sender_node_id.value,
        receiver_node_id=e.receiver_node_id.value,
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
# NodeResult
# ---------------------------------------------------------------------------


def node_result_model_to_entity(m: NodeResultModel) -> NodeResult:
    return NodeResult(
        id=NodeResultId(m.id),
        node_id=NodeId(m.node_id),
        workflow_id=WorkflowId(m.workflow_id),
        status=Status(m.status),
        stdout=m.stdout,
        stderr=m.stderr,
        artifact_uri=m.artifact_uri,
        created_at=_ensure_utc(m.created_at),
    )


def node_result_entity_to_model(r: NodeResult) -> NodeResultModel:
    return NodeResultModel(
        id=r.id.value,
        node_id=r.node_id.value,
        workflow_id=r.workflow_id.value,
        status=r.status.value,
        stdout=r.stdout,
        stderr=r.stderr,
        artifact_uri=r.artifact_uri,
        created_at=r.created_at,
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
    m: GraphDefinitionModel,
) -> GraphDefinition:
    return GraphDefinition(
        id=GraphDefinitionId(m.id),
        name=m.name,
        purpose=m.purpose,
        nodes=[graph_definition_node_model_to_entity(node) for node in m.nodes],
    )


def graph_definition_entity_to_model(
    graph: GraphDefinition,
) -> GraphDefinitionModel:
    m = GraphDefinitionModel(
        id=graph.id,
        name=graph.name,
        purpose=graph.purpose,
    )
    m.nodes = [
        graph_definition_node_entity_to_model(
            node,
            graph.id.value,
        )
        for node in graph.nodes
    ]
    return m


def graph_definition_node_model_to_entity(
    m: GraphDefinitionNodeModel,
) -> GraphDefinitionNode:
    return GraphDefinitionNode(
        id=GraphDefinitionNodeId(m.id),
        position=m.position,
        mode=Mode(m.mode),
        role=m.role,
        node_type=m.node_type,
        model=m.model or "",
        command=m.command,
        timeout=m.timeout,
        retries=m.retries,
        log_level=m.log_level,
        max_step=m.max_step,
        no_ask_user=bool(m.no_ask_user),
        autopilot=bool(m.autopilot),
        status_initial=m.status_initial,
        extra=dict(m.extra or {}),
        script=m.script or "",
        script_type=m.script_type or "",
    )


def graph_definition_node_entity_to_model(
    node: GraphDefinitionNode,
    graph_definition_id: str,
) -> GraphDefinitionNodeModel:
    return GraphDefinitionNodeModel(
        id=node.id.value,
        graph_definition_id=graph_definition_id,
        position=node.position,
        mode=node.mode.value,
        role=node.role,
        node_type=node.node_type,
        model=node.model,
        command=node.command,
        timeout=node.timeout,
        retries=node.retries,
        log_level=node.log_level,
        max_step=node.max_step,
        no_ask_user=node.no_ask_user,
        autopilot=node.autopilot,
        status_initial=node.status_initial,
        extra=node.extra,
        script=node.script,
        script_type=node.script_type,
    )
