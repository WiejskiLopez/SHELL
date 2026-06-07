"""Application DTOs — read-side data transfer objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class TaskDto:
    id: str
    name: str
    version: int
    hash: str
    is_current: bool
    created_at: datetime
    body_md: str
    template_graph_id: str
    graph_nodes: list[GraphNodeDto] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class GraphNodeDto:
    id: str
    position: int
    node_dir: str
    mode: str
    role: str
    node_type: str
    model: str
    command: str


@dataclass(frozen=True, slots=True)
class WorkflowDto:
    id: str
    task_name: str
    status: str
    created_at: datetime
    node_states: dict[str, NodeStateDto] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NodeStateDto:
    node_id: str
    status: str
    step: int
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class EnvelopeDto:
    id: str
    workflow_id: str
    sender_node_id: str
    receiver_node_id: str
    source_role: str
    target_role: str
    status: str
    stage: str
    step: int
    payload: dict[str, object]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NodeResultDto:
    id: str
    node_id: str
    workflow_id: str
    status: str
    stdout: str
    stderr: str
    artifact_uri: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PromptDto:
    id: str
    name: str
    version: int
    hash: str
    body: str
    is_current: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RunnerConfigDto:
    id: str
    package_name: str
    kind: str
    hash: str
    body: dict[str, object]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RagChunkDto:
    chunk_id: str
    document_id: str
    chunk_index: int
    chunk_text: str
    source_uri: str
    title: str
    domain: str
    score: float = 0.0


@dataclass(frozen=True, slots=True)
class MessageDto:
    id: str
    session_id: str
    correlation_id: str
    sender: str
    receiver: str
    payload: dict[str, object]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SessionDto:
    id: str
    goal: str
    status: str
    opened_at: datetime
    closed_at: datetime | None
    messages: list[MessageDto] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class GraphDto:
    id: str
    graph_template_id: str
    task_id: str


@dataclass(frozen=True, slots=True)
class TemplateGraphDto:
    id: str
    name: str
    purpose: str


@dataclass(frozen=True, slots=True)
class TemplateGraphNodeDto:
    id: str
    position: int
    node_dir: str
    mode: str
    role: str
    node_type: str
    model: str
    command: str
