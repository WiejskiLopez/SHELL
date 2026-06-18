"""InMemory persistence adapters for unit tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.application.dto.dto import (
    EnvelopeDto,
    MessageDto,
    GraphNodeExecutionResultDto,
    GraphNodeExecutionStateDto,
    PromptDto,
    RagChunkDto,
    RunnerConfigDto,
    SessionDto,
    TaskExecutionDto,
    WorkflowDto,
)
from shell.application.ports.unit_of_work import UnitOfWork
from shell.domain.entities.graph_definition import GraphDefinition
from shell.domain.entities.graph_node_definition import GraphNodeDefinition
from shell.domain.repositories.envelope_repository import (
    EnvelopeArchive,
    EnvelopeRepository,
)
from shell.domain.repositories.graph_definition_repository import (
    GraphNodeDefinitionRepository,
    GraphDefinitionRepository,
)
from shell.domain.repositories.graph_execution_repository import GraphExecutionRepository
from shell.domain.repositories.prompt_repository import PromptRepository
from shell.domain.repositories.rag_repository import RagDocumentRepository
from shell.domain.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.repositories.session_repository import SessionRepository
from shell.domain.repositories.task_execution_repository import TaskExecutionRepository
from shell.domain.repositories.workflow_repository import WorkflowRepository
from shell.domain.value_objects.envelope_status import EnvelopeStatus
from shell.domain.value_objects.execution_result import ExecutionResult
from shell.domain.value_objects.ids import (
    EnvelopeId,
    GraphDefinitionId,
    GraphNodeDefinitionId,
    GraphExecutionId,
    MessageId,
    GraphNodeExecutionId,
    GraphNodeExecutionResultId,
    PromptId,
    RagChunkId,
    RagDocumentId,
    RunnerConfigId,
    SessionId,
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.value_objects.mode import Mode

if TYPE_CHECKING:
    from shell.domain.entities.envelope import Envelope
    from shell.domain.entities.graph_execution import GraphExecution
    from shell.domain.entities.prompt import Prompt
    from shell.domain.entities.rag_document import RagChunk, RagDocument
    from shell.domain.entities.runner_config import RunnerConfig
    from shell.domain.entities.session import Message, Session
    from shell.domain.entities.task_execution import TaskExecution
    from shell.domain.entities.workflow import Workflow
    from shell.domain.events.events import DomainEvent
    from shell.domain.value_objects.manifest import Manifest
    from shell.domain.value_objects.task_execution_name import TaskExecutionName

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Repository fakes
# ---------------------------------------------------------------------------


class InMemoryTaskExecutionRepository(TaskExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, TaskExecution] = {}

    async def get_by_id(self, task_execution_id: TaskExecutionId) -> TaskExecution | None:
        return self._store.get(task_execution_id.value)

    async def get_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        for t in self._store.values():
            if t.name == name:
                return t
        return None

    async def get_current_by_id(self, task_execution_id: TaskExecutionId) -> TaskExecution | None:
        task_execution = self._store.get(task_execution_id.value)
        if task_execution and task_execution.is_current:
            return task_execution
        return None

    async def get_current_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        for t in self._store.values():
            if t.name == name and t.is_current:
                return t
        return None

    async def save(self, task_execution: TaskExecution) -> None:
        self._store[task_execution.id.value] = task_execution

    async def list_current(self) -> list[TaskExecution]:
        return [t for t in self._store.values() if t.is_current]


class InMemoryGraphExecutionRepository(GraphExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphExecution] = {}

    async def get_by_id(self, graph_execution_id: GraphExecutionId) -> GraphExecution | None:
        return self._store.get(graph_execution_id.value)

    async def get_by_task_execution_id(self, task_execution_id: TaskExecutionId) -> GraphExecution | None:
        for g in self._store.values():
            if g.task_execution_id == task_execution_id:
                return g
        return None

    async def save(self, graph_execution: GraphExecution) -> None:
        self._store[graph_execution.id.value] = graph_execution


class InMemoryWorkflowRepository(WorkflowRepository):
    """In-memory ``WorkflowRepository`` with optimistic concurrency control.

    Mirrors :class:`SqlWorkflowRepository` semantics so unit tests behave the
    same way as integration tests: ``save`` bumps ``Workflow.version`` and
    raises :class:`WorkflowConcurrentlyModified` if the persisted snapshot was
    written to by another caller. The persisted version is tracked
    independently of the in-memory aggregate to simulate the database row.
    """

    def __init__(self) -> None:
        self._store: dict[str, Workflow] = {}
        self._persisted_versions: dict[str, int] = {}

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        return self._store.get(workflow_id.value)

    async def save(self, workflow: Workflow) -> None:
        from shell.domain.exceptions import WorkflowConcurrentlyModified

        existing_version = self._persisted_versions.get(workflow.id.value)
        if existing_version is None:
            workflow.version = max(workflow.version, 0) + 1
            self._store[workflow.id.value] = workflow
            self._persisted_versions[workflow.id.value] = workflow.version
            return

        if existing_version != workflow.version:
            raise WorkflowConcurrentlyModified(workflow.id.value)

        workflow.version = workflow.version + 1
        self._store[workflow.id.value] = workflow
        self._persisted_versions[workflow.id.value] = workflow.version


class InMemoryEnvelopeRepository(EnvelopeRepository):
    def __init__(self) -> None:
        self._store: dict[str, Envelope] = {}

    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None:
        return self._store.get(envelope_id.value)

    async def save(self, envelope: Envelope) -> None:
        self._store[envelope.id.value] = envelope

    async def list_by_workflow(
        self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0
    ) -> list[Envelope]:
        results = [e for e in self._store.values() if e.workflow_id == workflow_id]
        results = results[offset:]
        if limit is not None:
            results = results[:limit]
        return results

    async def list_pending(
        self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0
    ) -> list[Envelope]:
        results = [
            e
            for e in self._store.values()
            if e.workflow_id == workflow_id and e.status == EnvelopeStatus.PENDING
        ]
        results = results[offset:]
        if limit is not None:
            results = results[:limit]
        return results


class InMemoryEnvelopeArchive(EnvelopeArchive):
    def __init__(self) -> None:
        self._store: dict[str, Envelope] = {}

    async def archive(self, envelope: Envelope) -> str:
        uri = f"memory://archive/{envelope.id.value}"
        self._store[uri] = envelope
        return uri

    async def get(self, archive_uri: str) -> Envelope | None:
        return self._store.get(archive_uri)


class InMemoryPromptRepository(PromptRepository):
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


class InMemoryRunnerConfigRepository(RunnerConfigRepository):
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


class InMemoryRagDocumentRepository(RagDocumentRepository):
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

        from shell.domain.services.rag_index_service import cosine_similarity

        dim = len(query_embedding) // 4
        query_vec = list(struct.unpack(f"{dim}f", query_embedding))
        scored: list[tuple[float, RagChunk]] = []
        for doc in self._store.values():
            if domain and doc.domain != domain:
                continue
            for chunk in doc.chunks:
                chunk_vec = list(struct.unpack(f"{len(chunk.embedding) // 4}f", chunk.embedding))
                score = cosine_similarity(query_vec, chunk_vec)
                scored.append((score, chunk))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [c for _, c in scored[:top_k]]


class InMemorySessionRepository(SessionRepository):
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


class InMemoryUnitOfWork(UnitOfWork):  # Jawne dziedziczenie (kontrakt)
    """InMemory UnitOfWork for fast unit and integration testing.

    Note on rollback: This implementation clears staged events and resets
    commit flags, but DOES NOT rollback the internal state of the
    InMemory repositories (dictionaries/lists). For pure unit tests,
    this is usually sufficient.
    """

    def __init__(self) -> None:
        # Private repository instances
        self._task_executions = InMemoryTaskExecutionRepository()
        self._graph_executions = InMemoryGraphExecutionRepository()
        self._workflows = InMemoryWorkflowRepository()
        self._envelopes = InMemoryEnvelopeRepository()
        self._prompts = InMemoryPromptRepository()
        self._runner_configs = InMemoryRunnerConfigRepository()
        self._envelope_archive = InMemoryEnvelopeArchive()
        self._rag_documents = InMemoryRagDocumentRepository()
        self._sessions = InMemorySessionRepository()
        self._graph_definitions = InMemoryGraphDefinitionRepository()

        # Stan transakcyjny
        self._committed = False
        self._staged_events: list[DomainEvent] = []
        self._committed_events: list[DomainEvent] = []

    # ------------------------------------------------------------------
    # Test Helpers (Seeders)
    # ------------------------------------------------------------------

    def seed_base_planner(self) -> None:
        """Helper method to inject a base planner for tests that require it.
        Keeps the default __init__ clean and maintains test isolation.
        """
        self._graph_definitions._store["base_planner"] = GraphDefinition(
            id=GraphDefinitionId("base-planner-id"),
            name="base_planner",
            purpose="default_planning",
            graph_node_definitions=[
                GraphNodeDefinition(
                    id=GraphNodeDefinitionId("base-planner-node-1"),
                    position=0,
                    mode=Mode("agent"),
                    role="agent",
                    node_type="agent",
                ),
            ],
        )

    # ------------------------------------------------------------------
    # Repository properties (covariant return types — mypy-friendly)
    # ------------------------------------------------------------------

    @property
    def task_executions(self) -> InMemoryTaskExecutionRepository:
        return self._task_executions

    @property
    def graph_executions(self) -> InMemoryGraphExecutionRepository:
        return self._graph_executions

    @property
    def workflows(self) -> InMemoryWorkflowRepository:
        return self._workflows

    @property
    def envelopes(self) -> InMemoryEnvelopeRepository:
        return self._envelopes

    @property
    def prompts(self) -> InMemoryPromptRepository:
        return self._prompts

    @property
    def runner_configs(self) -> InMemoryRunnerConfigRepository:
        return self._runner_configs

    @property
    def envelope_archive(self) -> InMemoryEnvelopeArchive:
        return self._envelope_archive

    @property
    def rag_documents(self) -> InMemoryRagDocumentRepository:
        return self._rag_documents

    @property
    def sessions(self) -> InMemorySessionRepository:
        return self._sessions

    @property
    def graph_definitions(self) -> InMemoryGraphDefinitionRepository:
        return self._graph_definitions

    # ------------------------------------------------------------------
    # Outbox staging — mirrors SqlAlchemyUnitOfWork interface
    # ------------------------------------------------------------------

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._staged_events.extend(events)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    @property
    def committed_events(self) -> list[DomainEvent]:
        return list(self._committed_events)

    # ------------------------------------------------------------------
    # Context Management & Transaction Control
    # ------------------------------------------------------------------

    async def __aenter__(self) -> InMemoryUnitOfWork:
        self._committed = False
        self._staged_events = []
        self._committed_events = []
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        self._committed_events = list(self._staged_events)
        self._staged_events = []
        self._committed = True

    async def rollback(self) -> None:
        self._staged_events = []
        self._committed_events = []
        self._committed = False


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

    def new_task_execution_id(self) -> TaskExecutionId:
        return TaskExecutionId(self._next())

    def new_workflow_id(self) -> WorkflowId:
        return WorkflowId(self._next())

    def new_envelope_id(self) -> EnvelopeId:
        return EnvelopeId(self._next())

    def new_prompt_id(self) -> PromptId:
        return PromptId(self._next())

    def new_graph_node_execution_result_id(self) -> GraphNodeExecutionResultId:
        return GraphNodeExecutionResultId(self._next())

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

    def new_graph_definition_id(self) -> GraphDefinitionId:
        return GraphDefinitionId(self._next())

    def new_graph_node_definition_id(self) -> GraphNodeDefinitionId:
        return GraphNodeDefinitionId(self._next())

    def new_graph_execution_id(self) -> GraphExecutionId:
        return GraphExecutionId(self._next())

    def new_graph_node_execution_id(self) -> GraphNodeExecutionId:
        return GraphNodeExecutionId(self._next())


class FakeEventPublisher:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class FakeLogger:
    """No-op implementation of the Logger port for use in unit tests."""

    def debug(self, msg: str, **kw: object) -> None:
        pass

    def info(self, msg: str, **kw: object) -> None:
        pass

    def warning(self, msg: str, **kw: object) -> None:
        pass

    def error(self, msg: str, **kw: object) -> None:
        pass


class FakeTaskLoader:
    def __init__(self, md: str = "# Task") -> None:
        self._md = md

    async def load(self, md_path: str) -> str:
        return self._md


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

    async def run(
        self,
        manifest: Manifest,
        workspace_path: str,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult:
        self.calls.append({"manifest": manifest, "workspace_path": workspace_path})
        return ExecutionResult(
            stdout=self._stdout,
            stderr=self._stderr,
            returncode=self._returncode,
        )


class FakeNodeWorkspace:
    """Fake workspace that performs no filesystem operations."""

    async def prepare(self, graph_node_execution_id: str, work_dir: str) -> str:
        return f"/fake/workspace/{graph_node_execution_id}"

    async def cleanup(self, workspace_path: str) -> None:
        pass


class InMemoryQueryServices:
    """Implementacja portów odczytu dla testów jednostkowych.
    Czyta dane bezpośrednio z magazynów InMemoryUnitOfWork i mapuje je na DTO.
    """

    def __init__(self, uow: InMemoryUnitOfWork) -> None:
        self._uow = uow

    async def get_task_execution_by_name(self, name: str) -> TaskExecutionDto | None:
        # Przeszukujemy magazyn zadań w repozytorium in-memory
        task_execution = next(
            (t for t in self._uow.task_executions._store.values() if t.name.value == name),  # type: ignore[attr-defined]
            None,
        )
        if not task_execution:
            return None
        graph_execution = await self._uow.graph_executions.get_by_task_execution_id(task_execution.id)
        graph_node_executions = []
        if graph_execution is not None:
            from shell.application.dto.dto import GraphNodeExecutionDto

            graph_node_executions = [
                GraphNodeExecutionDto(
                    id=n.id.value,
                    position=n.position,
                    node_dir=n.node_dir,
                    mode=n.mode.value,
                    role=n.role,
                    node_type=n.node_type,
                    model=n.model,
                    command=n.command,
                )
                for n in graph_execution.graph_node_executions
            ]
        return TaskExecutionDto(
            id=task_execution.id.value,
            name=task_execution.name.value,
            version=task_execution.version.value,
            hash=task_execution.hash.value,
            is_current=task_execution.is_current,
            created_at=task_execution.created_at,
            body=task_execution.body.value,
            graph_node_executions=graph_node_executions,
        )

    async def get_current_task(self, name: str) -> TaskExecutionDto | None:
        return await self.get_task_execution_by_name(name)

    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None:

        workflow = self._uow.workflows._store.get(workflow_id)  # type: ignore[attr-defined]
        if not workflow:
            return None
        return WorkflowDto(
            id=str(workflow.id),
            task_execution_id=str(workflow.task_execution_id),
            status=workflow.status.value,
            created_at=workflow.created_at,
            graph_node_execution_states={
                str(graph_node_execution_id): GraphNodeExecutionStateDto(
                    graph_node_execution_id=str(s.graph_node_execution_id),
                    status=s.status.value,
                    step=s.step,
                    updated_at=s.updated_at,
                )
                for graph_node_execution_id, s in workflow.graph_node_execution_states.items()
            },
        )

    async def get_envelopes_by_workflow(
        self, workflow_id: str, pending_only: bool = False
    ) -> list[EnvelopeDto]:
        envelopes = [
            e
            for e in self._uow.envelopes._store.values()
            if str(e.workflow_id) == workflow_id  # type: ignore[attr-defined]
        ]
        if pending_only:
            envelopes = [e for e in envelopes if e.status.value == "pending"]

        return [
            EnvelopeDto(
                id=str(e.id),
                workflow_id=str(e.workflow_id),
                sender_graph_node_execution_id=str(e.sender_graph_node_execution_id),
                receiver_graph_node_execution_id=str(e.receiver_graph_node_execution_id),
                source_role=e.source_role,
                target_role=e.target_role,
                status=e.status.value,
                stage=e.stage.value,
                step=e.step,
                payload=e.payload,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
            for e in envelopes
        ]

    async def get_graph_node_execution_result(self, graph_node_execution_id: str, workflow_id: str) -> GraphNodeExecutionResultDto | None:
        wf = await self._uow.workflows.get_by_id(WorkflowId(workflow_id))
        if wf is None:
            return None
        res = wf.graph_node_execution_results.get(graph_node_execution_id)
        if not res:
            return None
        return GraphNodeExecutionResultDto(
            id=str(res.id),
            graph_node_execution_id=str(res.graph_node_execution_id),
            workflow_id=str(res.workflow_id),
            status=res.status.value,
            stdout=res.stdout,
            stderr=res.stderr,
            artifact_uri=res.artifact_uri,
            created_at=res.created_at,
        )

    async def get_prompt(self, name: str) -> PromptDto | None:
        prompt = next(
            (p for p in self._uow.prompts._store.values() if p.name == name and p.is_current),
            None,  # type: ignore[attr-defined]
        )
        if not prompt:
            return None
        return PromptDto(
            id=str(prompt.id),
            name=prompt.name,
            version=prompt.version,
            hash=str(prompt.hash),
            body=prompt.body,
            is_current=prompt.is_current,
            created_at=prompt.created_at,
        )

    async def get_runner_config(self, package_name: str) -> RunnerConfigDto | None:
        c = await self._uow.runner_configs.get_by_package(package_name)
        if not c:
            return None
        return RunnerConfigDto(
            id=str(c.id),
            package_name=c.package_name,
            kind=c.kind,
            hash=str(c.hash),
            body=c.body,
            created_at=c.created_at,
        )

    async def get_session_history(self, session_id: str) -> SessionDto | None:
        session = self._uow.sessions._store.get(session_id)  # type: ignore[attr-defined]

        if session is None:
            return None

        return SessionDto(
            id=session.id.value,
            goal=session.goal,
            status=session.status,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
            messages=[
                MessageDto(
                    id=message.id.value,
                    session_id=message.session_id.value,
                    correlation_id=message.correlation_id.value,
                    sender=message.sender,
                    receiver=message.receiver,
                    payload=message.payload,
                    created_at=message.created_at,
                )
                for message in session.messages
            ],
        )

    async def search_similar(
        self, query_embedding: bytes, top_k: int = 5, domain: str | None = None
    ) -> list[RagChunkDto]:
        # Prosta implementacja dla testów
        chunks = list(self._uow.rag_documents._store.values())  # type: ignore[attr-defined]
        return [
            RagChunkDto(
                chunk_id=f"chunk-{i}",
                document_id="doc-1",
                chunk_index=i,
                chunk_text="test content",
                source_uri="file://test.md",
                title="Test Doc",
                domain=domain or "default",
                score=1.0,
            )
            for i in range(min(top_k, len(chunks)))
        ]


class InMemoryGraphDefinitionRepository(GraphDefinitionRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphDefinition] = {}

    async def get(self, graph_definition_id: GraphDefinitionId) -> GraphDefinition | None:
        return self._store.get(graph_definition_id.value)

    async def get_graph_definition_by_name(self, name: str) -> GraphDefinition | None:
        for g in self._store.values():
            if g.name == name:
                return g
        return None

    async def get_by_id(self, id_: GraphDefinitionId) -> GraphDefinition | None:
        return self._store.get(id_.value)

    async def save(self, graph: GraphDefinition) -> None:
        self._store[graph.id.value] = graph


class InMemoryGraphNodeDefinitionRepository(GraphNodeDefinitionRepository):
    def __init__(self) -> None:
        self._store: dict[str, GraphNodeDefinition] = {}

    async def get_by_id(self, graph_node_definition_id: GraphNodeDefinitionId) -> GraphNodeDefinition | None:
        return self._store.get(graph_node_definition_id.value)

    async def save(self, node: GraphNodeDefinition) -> None:
        self._store[node.id.value] = node
