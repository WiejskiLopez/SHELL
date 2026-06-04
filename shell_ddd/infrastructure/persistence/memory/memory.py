"""InMemory persistence adapters for unit tests."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.envelope_status import EnvelopeStatus
from shell_ddd.domain.value_objects.ids import (
    EnvelopeId,
    MessageId,
    NodeId,
    NodeResultId,
    PromptId,
    RagChunkId,
    RagDocumentId,
    RunnerConfigId,
    SessionId,
    TaskId,
    WorkflowId,
)

if TYPE_CHECKING:
    from shell_ddd.domain.entities.envelope import Envelope
    from shell_ddd.domain.entities.node_result import NodeResult
    from shell_ddd.domain.entities.prompt import Prompt
    from shell_ddd.domain.entities.rag_document import RagChunk, RagDocument
    from shell_ddd.domain.entities.runner_config import RunnerConfig
    from shell_ddd.domain.entities.session import Message, Session
    from shell_ddd.domain.entities.task import Task
    from shell_ddd.domain.entities.workflow import Workflow
    from shell_ddd.domain.events.events import DomainEvent
    from shell_ddd.domain.value_objects.task_name import TaskName


# ---------------------------------------------------------------------------
# Repository fakes
# ---------------------------------------------------------------------------


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._store: dict[str, Task] = {}

    async def get_by_id(self, task_id: TaskId) -> Task | None:
        return self._store.get(task_id.value)

    async def get_by_name(self, name: TaskName) -> Task | None:
        for t in self._store.values():
            if t.name == name:
                return t
        return None

    async def get_current_by_name(self, name: TaskName) -> Task | None:
        for t in self._store.values():
            if t.name == name and t.is_current:
                return t
        return None

    async def save(self, task: Task) -> None:
        self._store[task.id.value] = task

    async def list_current(self) -> list[Task]:
        return [t for t in self._store.values() if t.is_current]


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self._store: dict[str, Workflow] = {}

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        return self._store.get(workflow_id.value)

    async def save(self, workflow: Workflow) -> None:
        self._store[workflow.id.value] = workflow


class InMemoryEnvelopeRepository:
    def __init__(self) -> None:
        self._store: dict[str, Envelope] = {}

    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None:
        return self._store.get(envelope_id.value)

    async def save(self, envelope: Envelope) -> None:
        self._store[envelope.id.value] = envelope

    async def list_by_workflow(self, workflow_id: WorkflowId) -> list[Envelope]:
        return [e for e in self._store.values() if e.workflow_id == workflow_id]

    async def list_pending(self, workflow_id: WorkflowId) -> list[Envelope]:
        return [
            e
            for e in self._store.values()
            if e.workflow_id == workflow_id and e.status == EnvelopeStatus.PENDING
        ]


class InMemoryEnvelopeArchive:
    def __init__(self) -> None:
        self._store: dict[str, Envelope] = {}

    async def archive(self, envelope: Envelope) -> str:
        uri = f"memory://archive/{envelope.id.value}"
        self._store[uri] = envelope
        return uri

    async def get(self, archive_uri: str) -> Envelope | None:
        return self._store.get(archive_uri)


class InMemoryPromptRepository:
    def __init__(self) -> None:
        self._store: dict[str, Prompt] = {}

    async def get_by_id(self, prompt_id: PromptId) -> Prompt | None:
        return self._store.get(prompt_id.value)

    async def get_current_by_name(self, name: str) -> Prompt | None:
        for p in self._store.values():
            if p.name == name and p.is_current:
                return p
        return None

    async def save(self, prompt: Prompt) -> None:
        self._store[prompt.id.value] = prompt


class InMemoryNodeResultRepository:
    def __init__(self) -> None:
        self._store: dict[str, NodeResult] = {}

    async def get_by_id(self, result_id: NodeResultId) -> NodeResult | None:
        return self._store.get(result_id.value)

    async def get_by_node_and_workflow(
        self, node_id: NodeId, workflow_id: WorkflowId
    ) -> NodeResult | None:
        for r in self._store.values():
            if r.node_id == node_id and r.workflow_id == workflow_id:
                return r
        return None

    async def save(self, result: NodeResult) -> None:
        self._store[result.id.value] = result


class InMemoryRunnerConfigRepository:
    def __init__(self) -> None:
        self._store: dict[str, RunnerConfig] = {}

    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None:
        return self._store.get(config_id.value)

    async def get_by_package(self, package_name: str) -> RunnerConfig | None:
        for c in self._store.values():
            if c.package_name == package_name:
                return c
        return None

    async def save(self, config: RunnerConfig) -> None:
        self._store[config.id.value] = config


class InMemoryRagDocumentRepository:
    def __init__(self) -> None:
        self._store: dict[str, RagDocument] = {}

    async def save(self, document: RagDocument) -> None:
        self._store[document.id.value] = document

    async def get_by_id(self, doc_id: RagDocumentId) -> RagDocument | None:
        return self._store.get(doc_id.value)

    async def search_similar(
        self,
        query_embedding: bytes,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RagChunk]:
        import struct
        from shell_ddd.domain.services.rag_index_service import cosine_similarity

        dim = len(query_embedding) // 4
        query_vec = list(struct.unpack(f"{dim}f", query_embedding))
        scored: list[tuple[float, RagChunk]] = []
        for doc in self._store.values():
            if domain and doc.domain != domain:
                continue
            for chunk in doc.chunks:
                chunk_vec = list(
                    struct.unpack(f"{len(chunk.embedding) // 4}f", chunk.embedding)
                )
                score = cosine_similarity(query_vec, chunk_vec)
                scored.append((score, chunk))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [c for _, c in scored[:top_k]]


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._store: dict[str, Session] = {}
        self._messages: dict[str, list[Message]] = {}

    async def save(self, session: Session) -> None:
        self._store[session.id.value] = session
        # persist messages accumulated on the entity
        existing = self._messages.get(session.id.value, [])
        existing_ids = {m.id.value for m in existing}
        for msg in session.messages:
            if msg.id.value not in existing_ids:
                existing.append(msg)
        self._messages[session.id.value] = existing

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        return self._store.get(session_id.value)

    async def get_messages(self, session_id: SessionId) -> list[Message]:
        return list(self._messages.get(session_id.value, []))


# ---------------------------------------------------------------------------
# UnitOfWork fake
# ---------------------------------------------------------------------------


class InMemoryUnitOfWork:
    def __init__(self) -> None:
        self.tasks = InMemoryTaskRepository()
        self.workflows = InMemoryWorkflowRepository()
        self.envelopes = InMemoryEnvelopeRepository()
        self.prompts = InMemoryPromptRepository()
        self.node_results = InMemoryNodeResultRepository()
        self.runner_configs = InMemoryRunnerConfigRepository()
        self.envelope_archive = InMemoryEnvelopeArchive()
        self.rag_documents = InMemoryRagDocumentRepository()
        self.sessions = InMemorySessionRepository()
        self._committed = False

    async def commit(self) -> None:
        self._committed = True

    async def rollback(self) -> None:
        pass

    async def __aenter__(self) -> InMemoryUnitOfWork:
        self._committed = False
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


# ---------------------------------------------------------------------------
# Port fakes (Clock, IdGenerator, EventPublisher)
# ---------------------------------------------------------------------------


class FakeClock:
    def __init__(self, fixed: datetime | None = None) -> None:
        self._time = fixed or datetime(2024, 1, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self._time


class FakeIdGenerator:
    def __init__(self) -> None:
        self._counter = 0

    def _next(self) -> str:
        self._counter += 1
        return f"00000000-0000-0000-0000-{self._counter:012d}"

    def new_task_id(self) -> TaskId:
        return TaskId(self._next())

    def new_workflow_id(self) -> WorkflowId:
        return WorkflowId(self._next())

    def new_envelope_id(self) -> EnvelopeId:
        return EnvelopeId(self._next())

    def new_prompt_id(self) -> PromptId:
        return PromptId(self._next())

    def new_node_result_id(self) -> NodeResultId:
        return NodeResultId(self._next())

    def new_runner_config_id(self) -> RunnerConfigId:
        return RunnerConfigId(self._next())

    def new_rag_document_id(self) -> RagDocumentId:
        return RagDocumentId(self._next())

    def new_rag_chunk_id(self) -> RagChunkId:
        return RagChunkId(self._next())

    def new_session_id(self) -> SessionId:
        return SessionId(self._next())

    def new_message_id(self) -> MessageId:
        return MessageId(self._next())


class FakeEventPublisher:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class FakeTaskLoader:
    def __init__(self, md: str = "# Task", yaml_raw: str = "graph: []") -> None:
        self._md = md
        self._yaml = yaml_raw

    async def load(self, md_path: str, yaml_path: str) -> tuple[str, str]:
        return self._md, self._yaml


# ---------------------------------------------------------------------------
# Fake NodeProcessRunner / NodeWorkspace (for unit tests and bootstrap stub)
# ---------------------------------------------------------------------------


class FakeNodeProcessRunner:
    """Fake runner returning configurable ExecutionResult."""

    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self._stdout = stdout
        self._stderr = stderr
        self._returncode = returncode
        self.calls: list[dict[str, object]] = []

    async def run(self, manifest: object, workspace_path: str, env: dict | None = None) -> object:
        from shell_ddd.domain.value_objects.execution_result import ExecutionResult

        self.calls.append({"manifest": manifest, "workspace_path": workspace_path})
        return ExecutionResult(
            stdout=self._stdout,
            stderr=self._stderr,
            returncode=self._returncode,
        )


class FakeNodeWorkspace:
    """Fake workspace that performs no filesystem operations."""

    async def prepare(self, node_id: str, work_dir: str) -> str:
        return f"/fake/workspace/{node_id}"

    async def cleanup(self, workspace_path: str) -> None:
        pass
