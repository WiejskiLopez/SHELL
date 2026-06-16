"""SQL ORM model <-> domain entity mappers."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.entities.envelope import Envelope, EnvelopeEvent
from shell.domain.entities.graph import Graph
from shell.domain.entities.graph_node import GraphNode
from shell.domain.entities.node_result import NodeResult
from shell.domain.entities.prompt import Prompt
from shell.domain.entities.runner_config import RunnerConfig
from shell.domain.entities.task import Task
from shell.domain.entities.template_graph import TemplateGraph
from shell.domain.entities.template_graph_node import TemplateGraphNode
from shell.domain.entities.workflow import NodeState, Workflow
from shell.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell.domain.value_objects.hash import Hash
from shell.domain.value_objects.ids import (
    EnvelopeEventId,
    EnvelopeId,
    GraphId,
    NodeId,
    NodeResultId,
    NodeStateId,
    PromptId,
    RunnerConfigId,
    TaskId,
    TemplateGraphId,
    TemplateGraphNodeId,
    WorkflowId,
)
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.status import Status
from shell.domain.value_objects.task_body import TaskBody
from shell.domain.value_objects.task_name import TaskName
from shell.domain.value_objects.version import Version
from shell.infrastructure.persistence.sql.models import (
    EnvelopeEventModel,
    EnvelopeModel,
    GraphModel,
    GraphNodeModel,
    NodeResultModel,
    NodeStateModel,
    PromptModel,
    RunnerConfigModel,
    TaskModel,
    TemplateGraphModel,
    TemplateGraphNodeModel,
    WorkflowModel,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


def task_model_to_entity(m: TaskModel) -> Task:
    return Task(
        id=TaskId(m.id),
        name=TaskName(m.name),
        version=Version(m.version),
        hash=Hash(m.hash),
        body=TaskBody(m.body),
        is_current=m.is_current,
        created_at=_ensure_utc(m.created_at),
    )


def task_entity_to_model(task: Task) -> TaskModel:
    return TaskModel(
        id=task.id.value,
        name=task.name.value,
        version=task.version.value,
        hash=task.hash.value,
        body=task.body.value,
        is_current=task.is_current,
        created_at=task.created_at,
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
            task_id=n.task_id,
            source_dir=n.source_dir,
            work_dir=n.work_dir,
            status_initial=n.status_initial,
            extra=dict(n.extra),
        )
        for n in m.nodes
    ]
    return Graph(
        id=GraphId(m.id),
        task_id=TaskId(m.task_id),
        template_graph_id=TemplateGraphId(m.template_graph_id),
        raw_dict=dict(m.raw_dict),
        nodes=nodes,
    )


def graph_entity_to_model(graph: Graph) -> GraphModel:
    m = GraphModel(
        id=graph.id.value,
        task_id=graph.task_id.value,
        template_graph_id=str(graph.template_graph_id),
        raw_dict=dict(graph.raw_dict),
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
            task_id=n.task_id,
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
        task_id=TaskId(m.task_id),
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
        task_id=w.task_id.value,
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
# TemplateGraph
# ---------------------------------------------------------------------------


def template_graph_model_to_entity(
    m: TemplateGraphModel,
) -> TemplateGraph:
    return TemplateGraph(
        id=TemplateGraphId(m.id),
        name=m.name,
        purpose=m.purpose,
        nodes=[template_graph_node_model_to_entity(node) for node in m.nodes],
    )


def template_graph_entity_to_model(
    graph: TemplateGraph,
) -> TemplateGraphModel:
    m = TemplateGraphModel(
        id=graph.id,
        name=graph.name,
        purpose=graph.purpose,
    )
    m.nodes = [
        template_graph_node_entity_to_model(
            node,
            graph.id.value,
        )
        for node in graph.nodes
    ]
    return m


def template_graph_node_model_to_entity(
    m: TemplateGraphNodeModel,
) -> TemplateGraphNode:
    return TemplateGraphNode(
        id=TemplateGraphNodeId(m.id),
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


def template_graph_node_entity_to_model(
    node: TemplateGraphNode,
    template_graph_id: str,
) -> TemplateGraphNodeModel:
    return TemplateGraphNodeModel(
        id=node.id.value,
        template_graph_id=template_graph_id,
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
