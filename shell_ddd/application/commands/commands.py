"""Application commands."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ImportTaskCommand:
    """Import a task from markdown + yaml files."""

    md_path: str
    task_name: str


@dataclass(frozen=True, slots=True)
class StartWorkflowCommand:
    """Start a new workflow for a given task."""

    task_name: str


@dataclass(frozen=True, slots=True)
class RunNodeCommand:
    """Execute a node within a workflow."""

    workflow_id: str
    node_id: str
    workspace_path: str


@dataclass(frozen=True, slots=True)
class RouteEnvelopesCommand:
    """Process pending envelopes for a workflow."""

    workflow_id: str


@dataclass(frozen=True, slots=True)
class ArchiveEnvelopeCommand:
    """Archive a delivered envelope."""

    envelope_id: str


@dataclass(frozen=True, slots=True)
class SaveNodeResultCommand:
    """Persist the result of a node execution."""

    workflow_id: str
    node_id: str
    status: str
    stdout: str = ""
    stderr: str = ""
    artifact_uri: str = ""


@dataclass(frozen=True, slots=True)
class SavePromptCommand:
    """Upsert a prompt by name."""

    name: str
    body: str
    source_uri: str = ""


@dataclass(frozen=True, slots=True)
class BootstrapRunnerConfigCommand:
    """Persist runner configuration for a package."""

    package_name: str
    kind: str
    body: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class IndexDocumentCommand:
    """Chunk, embed and index a text document for RAG retrieval."""

    source_uri: str
    title: str
    domain: str
    text: str
    chunk_size: int = 500
    overlap: int = 50


@dataclass(frozen=True, slots=True)
class OpenSessionCommand:
    """Open a new conversation session."""

    goal: str


@dataclass(frozen=True, slots=True)
class CloseSessionCommand:
    """Close an existing session."""

    session_id: str


@dataclass(frozen=True, slots=True)
class AppendMessageCommand:
    """Append a message to an open session."""

    session_id: str
    correlation_id: str
    sender: str
    receiver: str
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunTaskerWorkflowCommand:
    """Execute all graph nodes of a task concurrently (tasker orchestration)."""

    task_name: str
    work_dir: str
    max_parallel: int = 4
