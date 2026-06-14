"""InMemory persistence adapters for unit tests."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell_ddd.application.dto.dto import (
    EnvelopeDto,
    MessageDto,
    NodeResultDto,
    NodeStateDto,
    PromptDto,
    RagChunkDto,
    RunnerConfigDto,
    SessionDto,
    TaskDto,
    WorkflowDto,
)
from shell_ddd.domain.entities.template_graph import TemplateGraph
from shell_ddd.domain.entities.template_graph_node import TemplateGraphNode
from shell_ddd.domain.value_objects.envelope_status import EnvelopeStatus
from shell_ddd.domain.value_objects.ids import (
    EnvelopeId,
    GraphId,
    MessageId,
    NodeId,
    NodeResultId,
    PromptId,
    RagChunkId,
    RagDocumentId,
    RunnerConfigId,
    SessionId,
    TaskId,
    TemplateGraphId,
    TemplateGraphNodeId,
    WorkflowId,
)
from shell_ddd.domain.value_objects.mode import Mode

if TYPE_CHECKING:
    from shell_ddd.application.ports.messaging import EventPublisher
    from shell_ddd.domain.entities.envelope import Envelope
    from shell_ddd.domain.entities.graph import Graph
    from shell_ddd.domain.entities.prompt import Prompt
    from shell_ddd.domain.entities.rag_document import RagChunk, RagDocument
    from shell_ddd.domain.entities.runner_config import RunnerConfig
    from shell_ddd.domain.entities.session import Message, Session
    from shell_ddd.domain.entities.task import Task
    from shell_ddd.domain.entities.workflow import Workflow
    from shell_ddd.domain.events.events import DomainEvent
    from shell_ddd.domain.value_objects.task_name import TaskName

import logging

logger = logging.getLogger(__name__)


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


class InMemoryGraphRepository:
    def __init__(self) -> None:
        self._store: dict[str, Graph] = {}

    async def get_by_id(self, graph_id: GraphId) -> Graph | None:
        return self._store.get(graph_id.value)

    async def get_by_task_id(self, task_id: TaskId) -> Graph | None:
        for g in self._store.values():
            if g.task_id == task_id:
                return g
        return None

    async def save(self, graph: Graph) -> None:
        self._store[graph.id.value] = graph


class InMemoryWorkflowRepository:
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
        from shell_ddd.domain.exceptions import WorkflowConcurrentlyModified

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


class InMemoryEnvelopeRepository:
    def __init__(self) -> None:
        self._store: dict[str, Envelope] = {}

    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None:
        return self._store.get(envelope_id.value)

    async def save(self, envelope: Envelope) -> None:
        self._store[envelope.id.value] = envelope

    async def list_by_workflow(self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0) -> list[Envelope]:
        results = [e for e in self._store.values() if e.workflow_id == workflow_id]
        results = results[offset:]
        if limit is not None:
            results = results[:limit]
        return results

    async def list_pending(self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0) -> list[Envelope]:
        results = [
            e
            for e in self._store.values()
            if e.workflow_id == workflow_id and e.status == EnvelopeStatus.PENDING
        ]
        results = results[offset:]
        if limit is not None:
            results = results[:limit]
        return results


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
    def __init__(
        self,
        post_commit_publisher: EventPublisher | None = None,
    ) -> None:
        self._post_commit_publisher = post_commit_publisher
        self.tasks = InMemoryTaskRepository()
        self.graphs = InMemoryGraphRepository()
        self.workflows = InMemoryWorkflowRepository()
        self.envelopes = InMemoryEnvelopeRepository()
        self.prompts = InMemoryPromptRepository()
        self.runner_configs = InMemoryRunnerConfigRepository()
        self.envelope_archive = InMemoryEnvelopeArchive()
        self.rag_documents = InMemoryRagDocumentRepository()
        self.sessions = InMemorySessionRepository()
        self.template_graphs = InMemoryTemplateGraphRepository()
        # 🔥 SEED
        self.template_graphs._store["base_planner"] = TemplateGraph(
            id=TemplateGraphId("base-planner-id"),
            name="base_planner",
            purpose="default_planning",
            nodes=[
                TemplateGraphNode(
                    id=TemplateGraphNodeId("base-planner-node-1"),
                    position=0,
                    mode=Mode("agent"),
                    role="agent",
                    node_type="agent",
                ),
            ],
        )

        self._committed = False
        self._staged_events: list[DomainEvent] = []
        self._post_commit_buffer: list[DomainEvent] = []

    # ------------------------------------------------------------------
    # Outbox staging — mirrors SqlAlchemyUnitOfWork interface
    # ------------------------------------------------------------------

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._staged_events.extend(events)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    async def commit(self) -> None:
        self._post_commit_buffer = list(self._staged_events)
        self._staged_events = []
        self._committed = True

    async def rollback(self) -> None:
        self._staged_events = []
        self._post_commit_buffer = []
        self._committed = False

    async def __aenter__(self) -> InMemoryUnitOfWork:
        self._committed = False
        self._staged_events = []
        self._post_commit_buffer = []
        return self

    async def __aexit__(self, exc_type: object, *args: object) -> None:
        # Best-effort post-commit fan-out. Outbox staging happened atomically
        # with state changes inside ``commit()`` (durable source of truth).
        if exc_type is None and self._committed and self._post_commit_publisher is not None:
            buffered = self._post_commit_buffer
            self._post_commit_buffer = []
            await self._post_commit_publisher.publish(buffered)


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

    def new_template_graph_id(self) -> TemplateGraphId:
        return TemplateGraphId(self._next())

    def new_template_graph_node_id(self) -> TemplateGraphNodeId:
        return TemplateGraphNodeId(self._next())

    def new_graph_id(self) -> GraphId:
        return GraphId(self._next())

    def new_node_id(self) -> NodeId:
        return NodeId(self._next())


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


class InMemoryQueryServices:
    """Implementacja portów odczytu dla testów jednostkowych.
    Czyta dane bezpośrednio z magazynów InMemoryUnitOfWork i mapuje je na DTO.
    """

    def __init__(self, uow: InMemoryUnitOfWork) -> None:
        self._uow = uow

    async def get_task_by_name(self, name: str) -> TaskDto | None:
        # Przeszukujemy magazyn zadań w repozytorium in-memory
        task = next(
            (t for t in self._uow.tasks._store.values() if t.name.value == name),
            None,
        )
        if not task:
            return None
        graph = await self._uow.graphs.get_by_task_id(task.id)
        graph_nodes = []
        if graph is not None:
            from shell_ddd.application.dto.dto import GraphNodeDto
            graph_nodes = [
                GraphNodeDto(
                    id=n.id.value,
                    position=n.position,
                    node_dir=n.node_dir,
                    mode=n.mode.value,
                    role=n.role,
                    node_type=n.node_type,
                    model=n.model,
                    command=n.command,
                )
                for n in graph.nodes
            ]
        return TaskDto(
            id=task.id.value,
            name=task.name.value,
            version=task.version.value,
            hash=task.hash.value,
            is_current=task.is_current,
            created_at=task.created_at,
            body=task.body.value,
            graph_nodes=graph_nodes,
        )

    async def get_current_task(self, name: str) -> TaskDto | None:
        return await self.get_task_by_name(name)

    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None:

        workflow = self._uow.workflows._store.get(workflow_id)
        if not workflow:
            return None
        return WorkflowDto(
            id=str(workflow.id),
            task_name=workflow.task_name,
            status=workflow.status.value,
            created_at=workflow.created_at,
            node_states={
                str(node_id): NodeStateDto(
                    node_id=str(s.node_id),
                    status=s.status.value,
                    step=s.step,
                    updated_at=s.updated_at
                )
                for node_id, s in workflow.node_states.items()
            }
        )

    async def get_envelopes_by_workflow(
            self, workflow_id: str, pending_only: bool = False
    ) -> list[EnvelopeDto]:
        envelopes = [
            e for e in self._uow.envelopes._store.values()
            if str(e.workflow_id) == workflow_id
        ]
        if pending_only:
            envelopes = [e for e in envelopes if e.status.value == "pending"]

        return [
            EnvelopeDto(
                id=str(e.id), workflow_id=str(e.workflow_id),
                destination_node=e.destination_node, status=e.status.value,
                payload=e.payload
            ) for e in envelopes
        ]

    async def get_node_result(self, node_id: str, workflow_id: str) -> NodeResultDto | None:
        wf = await self._uow.workflows.get_by_id(WorkflowId(workflow_id))
        if wf is None:
            return None
        res = wf.node_results.get(node_id)
        if not res:
            return None
        return NodeResultDto(
            id=str(res.id),
            node_id=res.node_id,
            workflow_id=str(res.workflow_id),
            status=res.status.value,
            stdout=res.stdout,
            stderr=res.stderr,
            artifact_uri=res.artifact_uri,
            created_at=res.created_at,
        )

    async def get_prompt(self, name: str) -> PromptDto | None:
        prompt = next((p for p in self._uow.prompts._store.values() if p.name == name and p.is_current), None)
        if not prompt:
            return None
        return PromptDto(
            id=str(prompt.id),
            name=prompt.name,
            version=prompt.version,
            hash=prompt.hash,
            body=prompt.body,
            is_current=prompt.is_current,
            created_at=prompt.created_at)

    async def get_runner_config(self, package_name: str) -> RunnerConfigDto | None:
        c = self._uow.runner_configs._store.get(package_name)
        if not c:
            return None
        return RunnerConfigDto(package_name=c.package_name, version=c.version, config=c.config)

    async def get_session_history(self, session_id: str) -> SessionDto | None:
        session = self._uow.sessions._store.get(session_id)

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
        chunks = list(self._uow.rag_documents._store.values())
        return [
            RagChunkDto(
                chunk_id=f"chunk-{i}",
                document_id="doc-1",
                chunk_index=i,
                chunk_text="test content",
                source_uri="file://test.md",
                title="Test Doc",
                domain=domain or "default",
                score=1.0
            ) for i in range(min(top_k, len(chunks)))
        ]


class InMemoryTemplateGraphRepository:
    def __init__(self) -> None:
        self._store: dict[str, TemplateGraph] = {}

    async def get_template_graph_by_name(self, name: str) -> TemplateGraph | None:
        for g in self._store.values():
            if g.name == name:
                return g
        return None

    async def get_by_id(self, id_: TemplateGraphId) -> TemplateGraph | None:
        return self._store.get(id_.value)

    async def save(self, graph: TemplateGraph) -> None:
        self._store[graph.id.value] = graph


class InMemoryTemplateGraphNodeRepository:
    def __init__(self) -> None:
        self._store: dict[str, TemplateGraphNode] = {}

    async def get_by_id(self, node_id: TemplateGraphNodeId) -> TemplateGraphNode | None:
        return self._store.get(node_id.value)

    async def save(self, node: TemplateGraphNode) -> None:
        self._store[node.id.value] = node
