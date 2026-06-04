"""Application-level ports (Protocols consumed by handlers)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime

    from shell_ddd.domain.events.events import DomainEvent
    from shell_ddd.domain.repositories.repositories import (
        EnvelopeArchive,
        EnvelopeRepository,
        NodeResultRepository,
        PromptRepository,
        RagDocumentRepository,
        RunnerConfigRepository,
        SessionRepository,
        TaskRepository,
        WorkflowRepository,
    )
    from shell_ddd.domain.value_objects.execution_result import ExecutionResult
    from shell_ddd.domain.value_objects.ids import (
        EnvelopeId,
        MessageId,
        NodeResultId,
        PromptId,
        RagChunkId,
        RagDocumentId,
        RunnerConfigId,
        SessionId,
        TaskId,
        WorkflowId,
    )
    from shell_ddd.domain.value_objects.manifest import Manifest


class UnitOfWork(Protocol):
    """Transactional boundary; concrete adapters implement __aenter__/__aexit__."""

    tasks: TaskRepository
    workflows: WorkflowRepository
    envelopes: EnvelopeRepository
    prompts: PromptRepository
    node_results: NodeResultRepository
    runner_configs: RunnerConfigRepository
    envelope_archive: EnvelopeArchive
    rag_documents: RagDocumentRepository
    sessions: SessionRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def __aenter__(self) -> UnitOfWork: ...
    async def __aexit__(self, *args: object) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def new_task_id(self) -> TaskId: ...
    def new_workflow_id(self) -> WorkflowId: ...
    def new_envelope_id(self) -> EnvelopeId: ...
    def new_prompt_id(self) -> PromptId: ...
    def new_node_result_id(self) -> NodeResultId: ...
    def new_runner_config_id(self) -> RunnerConfigId: ...
    def new_rag_document_id(self) -> RagDocumentId: ...
    def new_rag_chunk_id(self) -> RagChunkId: ...
    def new_session_id(self) -> SessionId: ...
    def new_message_id(self) -> MessageId: ...


class EventPublisher(Protocol):
    async def publish(self, events: list[DomainEvent]) -> None: ...


class Logger(Protocol):
    def debug(self, msg: str, **kw: object) -> None: ...
    def info(self, msg: str, **kw: object) -> None: ...
    def warning(self, msg: str, **kw: object) -> None: ...
    def error(self, msg: str, **kw: object) -> None: ...


class TaskLoader(Protocol):
    """Reads task markdown + yaml from the filesystem."""

    async def load(self, md_path: str, yaml_path: str) -> tuple[str, str]:
        """Return (body_md, body_yaml_raw)."""
        ...


class NodeWorkspace(Protocol):
    """Manages the filesystem workspace for a node execution."""

    async def prepare(self, node_id: str, work_dir: str) -> str:
        """Prepare workspace and return its path."""
        ...

    async def cleanup(self, workspace_path: str) -> None: ...


class NodeProcessRunner(Protocol):
    """Runs a node subprocess and returns its result."""

    async def run(
        self,
        manifest: Manifest,
        workspace_path: str,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult: ...
