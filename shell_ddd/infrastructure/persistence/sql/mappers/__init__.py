"""SQL ORM model <-> domain entity mappers."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from shell_ddd.domain.entities.envelope import Envelope, EnvelopeEvent
from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.entities.prompt import Prompt
from shell_ddd.domain.entities.runner_config import RunnerConfig
from shell_ddd.domain.entities.task import Graph, GraphNode, Task
from shell_ddd.domain.entities.workflow import NodeState, Workflow
from shell_ddd.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell_ddd.domain.value_objects.hash import Hash
from shell_ddd.domain.value_objects.ids import (
    EnvelopeId,
    GraphId,
    NodeId,
    NodeResultId,
    PromptId,
    RunnerConfigId,
    TaskId,
    WorkflowId,
)
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.status import Status
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.persistence.sql.models import (
    EnvelopeEventModel,
    EnvelopeModel,
    GraphModel,
    GraphNodeModel,
    NodeResultModel,
    NodeStateModel,
    PromptModel,
    RunnerConfigModel,
    TaskModel,
    WorkflowModel,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


def task_model_to_entity(m: TaskModel) -> Task:
    graph = None
    if m.graph:
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
                task_name=n.task_name,
                source_dir=n.source_dir,
                work_dir=n.work_dir,
                status_initial=n.status_initial,
                extra=dict(n.extra),
            )
            for n in m.graph.nodes
        ]
        graph = Graph(
            id=GraphId(m.graph.id),
            task_id=TaskId(m.id),
            raw_dict=dict(m.graph.raw_dict),
            nodes=nodes,
        )
    return Task(
        id=TaskId(m.id),
        name=TaskName(m.name),
        version=m.version,
        hash=Hash(m.hash),
        body_md=m.body_md,
        body_yaml_raw=m.body_yaml_raw,
        is_current=m.is_current,
        created_at=_ensure_utc(m.created_at),
        graph=graph,
    )


def task_entity_to_model(t: Task) -> TaskModel:
    m = TaskModel(
        id=t.id.value,
        name=t.name.value,
        version=t.version,
        hash=t.hash.value,
        body_md=t.body_md,
        body_yaml_raw=t.body_yaml_raw,
        is_current=t.is_current,
        created_at=t.created_at,
    )
    if t.graph:
        gm = GraphModel(
            id=t.graph.id.value,
            task_id=t.id.value,
            raw_dict=t.graph.raw_dict,
        )
        gm.nodes = [
            GraphNodeModel(
                id=n.id.value,
                graph_id=t.graph.id.value,
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
                task_name=n.task_name,
                source_dir=n.source_dir,
                work_dir=n.work_dir,
                status_initial=n.status_initial,
                extra=n.extra,
            )
            for n in t.graph.nodes
        ]
        m.graph = gm
    return m


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


def workflow_model_to_entity(m: WorkflowModel) -> Workflow:
    states = {
        ns.node_id: NodeState(
            node_id=NodeId(ns.node_id),
            status=Status(ns.status),
            step=ns.step,
            updated_at=_ensure_utc(ns.updated_at),
        )
        for ns in m.node_states
    }
    return Workflow(
        id=WorkflowId(m.id),
        task_name=m.task_name,
        status=Status(m.status),
        created_at=_ensure_utc(m.created_at),
        node_states=states,
    )


def workflow_entity_to_model(w: Workflow) -> WorkflowModel:
    m = WorkflowModel(
        id=w.id.value,
        task_name=w.task_name,
        status=w.status.value,
        created_at=w.created_at,
    )
    m.node_states = [
        NodeStateModel(
            id=str(uuid.uuid4()),
            workflow_id=w.id.value,
            node_id=ns.node_id.value,
            status=ns.status.value,
            step=ns.step,
            updated_at=ns.updated_at,
        )
        for ns in w.node_states.values()
    ]
    return m


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


def envelope_model_to_entity(m: EnvelopeModel) -> Envelope:
    evts = [
        EnvelopeEvent(
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
            id=str(uuid.uuid4()),
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
