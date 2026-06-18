"""Application DTOs — read-side data transfer objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class TaskExecutionDto:
    id: str
    parent_task_execution_id: str | None = None
    name: str = ""
    version: int = 0
    hash: str = ""
    is_current: bool = True
    created_at: datetime | None = None
    body: str = ""
    graph_node_executions: list[GraphNodeExecutionDto] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionDto:
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
    task_execution_id: str
    status: str
    created_at: datetime
    graph_node_execution_states: dict[str, GraphNodeExecutionStateDto] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionStateDto:
    graph_node_execution_id: str
    status: str
    step: int
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class EnvelopeDto:
    id: str
    workflow_id: str
    sender_graph_node_execution_id: str
    receiver_graph_node_execution_id: str
    source_role: str
    target_role: str
    status: str
    stage: str
    step: int
    payload: dict[str, object]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionResultDto:
    id: str
    graph_node_execution_id: str
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
class GraphExecutionDto:
    id: str
    graph_definition_id: str
    task_execution_id: str


@dataclass(frozen=True, slots=True)
class GraphDefinitionDto:
    id: str
    name: str
    purpose: str


@dataclass(frozen=True, slots=True)
class GraphNodeDefinitionDto:
    id: str
    position: int
    node_dir: str
    mode: str
    role: str
    node_type: str
    model: str
    command: str


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionInputPayloadDto:
    id: str
    graph_node_execution_id: str
    payload: dict
    is_current: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionOutputPayloadDto:
    id: str
    graph_node_execution_id: str
    payload: dict
    is_current: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TaskExecutionInputPayloadDto:
    id: str
    task_execution_id: str
    payload: dict
    is_current: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TaskExecutionOutputPayloadDto:
    id: str
    task_execution_id: str
    payload: dict
    is_current: bool
    created_at: datetime
