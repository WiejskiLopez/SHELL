### infrastructure/messaging/sql_outbox_publisher.py
```
"""SqlOutboxPublisher — EventPublisher adapter that writes to outbox_event table.

Events are stored in a dedicated DB session so they survive even if the caller's
transaction was already committed.  An OutboxRelay then reads them and fans them
out to the EventBus.
"""
from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING

from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell_ddd.domain.events.events import DomainEvent


class SqlOutboxPublisher:
    """Writes domain events to the ``outbox_event`` table (own session per call)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def publish(self, events: list[DomainEvent]) -> None:
        if not events:
            return
        async with self._session_factory() as session:
            for event in events:
                payload = {
                    f.name: str(getattr(event, f.name))
                    for f in dataclasses.fields(event)  # type: ignore[arg-type]
                    if f.name != "occurred_at"
                }
                session.add(
                    OutboxEventModel(
                        id=str(uuid.uuid4()),
                        event_type=type(event).__name__,
                        occurred_at=event.occurred_at,
                        payload=payload,
                        published_at=None,
                    )
                )
            await session.commit()
```

### infrastructure/persistence/__init__.py
```
"""SqlAlchemyUnitOfWork \u2014 transactional boundary for SQL backends."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shell_ddd.domain.entities.envelope import Envelope
from shell_ddd.infrastructure.persistence.sql.repositories import (
    SqlEnvelopeArchiveStub,
    SqlEnvelopeRepository,
    SqlNodeResultRepository,
    SqlPromptRepository,
    SqlRagDocumentRepository,
    SqlRunnerConfigRepository,
    SqlSessionRepository,
    SqlTaskRepository,
    SqlWorkflowRepository,
)


class SqlAlchemyUnitOfWork:
    """UnitOfWork backed by SQLAlchemy AsyncSession.

    Works for both SQLite (sqlite+aiosqlite) and PostgreSQL (postgresql+asyncpg).
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session: AsyncSession = self._factory()
        self.tasks = SqlTaskRepository(self._session)
        self.workflows = SqlWorkflowRepository(self._session)
        self.envelopes = SqlEnvelopeRepository(self._session)
        self.prompts = SqlPromptRepository(self._session)
        self.node_results = SqlNodeResultRepository(self._session)
        self.runner_configs = SqlRunnerConfigRepository(self._session)
        self.envelope_archive: SqlEnvelopeArchiveStub = SqlEnvelopeArchiveStub()
        self.rag_documents = SqlRagDocumentRepository(self._session)
        self.sessions = SqlSessionRepository(self._session)
        return self

    async def __aexit__(self, exc_type: object, *args: object) -> None:
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
```

### infrastructure/persistence/memory/__init__.py
```
```

### infrastructure/persistence/memory/memory.py
```
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
```

### infrastructure/persistence/migrations/__init__.py
```
"""Alembic migration helpers."""
from __future__ import annotations
```

### infrastructure/persistence/migrations/mongo/__init__.py
```
```

### infrastructure/persistence/migrations/sql/__init__.py
```
"""Alembic env.py for async SQLAlchemy migrations."""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from shell_ddd.infrastructure.persistence.sql.models import Base

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)  # type: ignore[arg-type]

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection)  -> None:  # type: ignore[no-untyped-def]
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_async_engine(url)
    async with connectable.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### infrastructure/persistence/migrations/sql/env.py
```
"""Alembic env.py for async SQLAlchemy migrations (SQLite + PostgreSQL)."""
from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from shell_ddd.infrastructure.persistence.sql.models import Base

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)  # type: ignore[arg-type]

target_metadata = Base.metadata


def _get_url() -> str:
    # Allow override via env var (used in CI/docker)
    return os.environ.get("SHELL_DDD_DATABASE_URL") or config.get_main_option("sqlalchemy.url") or ""


def run_migrations_offline() -> None:
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,  # type: ignore[arg-type]
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = _get_url()
    connectable = create_async_engine(url, echo=False, future=True)
    async with connectable.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### infrastructure/persistence/migrations/sql/versions/001_initial.py
```
"""Initial migration — creates all shell_ddd tables.

Revision ID: 001
Revises: 
Create Date: 2026-06-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("body_md", sa.Text, nullable=False, server_default=""),
        sa.Column("body_yaml_raw", sa.Text, nullable=False, server_default=""),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_task_name", "task", ["name"])

    op.create_table(
        "graph",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("task.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("raw_dict", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_graph_task_id", "graph", ["task_id"])

    op.create_table(
        "graph_node",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_id",
            sa.String(36),
            sa.ForeignKey("graph.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("node_dir", sa.String(512), nullable=False, server_default=""),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("role", sa.String(128), nullable=False, server_default=""),
        sa.Column("node_type", sa.String(64), nullable=False, server_default=""),
        sa.Column("model", sa.String(128), nullable=False, server_default=""),
        sa.Column("command", sa.Text, nullable=False, server_default=""),
        sa.Column("timeout", sa.Integer, nullable=False, server_default="0"),
        sa.Column("retries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("log_level", sa.String(16), nullable=False, server_default="INFO"),
        sa.Column("max_step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("no_ask_user", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("autopilot", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("task_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("source_dir", sa.String(512), nullable=False, server_default=""),
        sa.Column("work_dir", sa.String(512), nullable=False, server_default=""),
        sa.Column("status_initial", sa.String(64), nullable=False, server_default=""),
        sa.Column("extra", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_graph_node_graph_id", "graph_node", ["graph_id"])

    op.create_table(
        "workflow",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="idle"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workflow_task_name", "workflow", ["task_name"])

    op.create_table(
        "node_state",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "workflow_id",
            sa.String(36),
            sa.ForeignKey("workflow.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("node_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="idle"),
        sa.Column("step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_node_state_workflow_id", "node_state", ["workflow_id"])

    op.create_table(
        "envelope",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=False, server_default=""),
        sa.Column("sender_node_id", sa.String(255), nullable=False),
        sa.Column("receiver_node_id", sa.String(255), nullable=False),
        sa.Column("source_role", sa.String(128), nullable=False, server_default=""),
        sa.Column("target_role", sa.String(128), nullable=False, server_default=""),
        sa.Column("sequence_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column("step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("stage", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("artifact_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("archive_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_envelope_workflow_id", "envelope", ["workflow_id"])

    op.create_table(
        "envelope_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "envelope_id",
            sa.String(36),
            sa.ForeignKey("envelope.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_envelope_event_envelope_id", "envelope_event", ["envelope_id"])

    op.create_table(
        "node_result",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("node_id", sa.String(255), nullable=False),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("stdout", sa.Text, nullable=False, server_default=""),
        sa.Column("stderr", sa.Text, nullable=False, server_default=""),
        sa.Column("artifact_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_node_result_node_id", "node_result", ["node_id"])
    op.create_index("ix_node_result_workflow_id", "node_result", ["workflow_id"])

    op.create_table(
        "prompt",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("source_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prompt_name", "prompt", ["name"])

    op.create_table(
        "runner_config",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("package_name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("body", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_runner_config_package_name", "runner_config", ["package_name"])

    # Envelope archive (optional — used by FileSystemEnvelopeArchive but kept for SQL completeness)
    op.create_table(
        "envelope_archive",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("envelope_id", sa.String(36), nullable=False),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("archive_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_envelope_archive_workflow_id", "envelope_archive", ["workflow_id"])
    op.create_index("ix_envelope_archive_envelope_id", "envelope_archive", ["envelope_id"])


def downgrade() -> None:
    op.drop_table("envelope_archive")
    op.drop_table("runner_config")
    op.drop_table("prompt")
    op.drop_table("node_result")
    op.drop_table("envelope_event")
    op.drop_table("envelope")
    op.drop_table("node_state")
    op.drop_table("workflow")
    op.drop_table("graph_node")
    op.drop_table("graph")
    op.drop_table("task")
```

### infrastructure/persistence/migrations/sql/versions/002_memory_rag.py
```
"""Faza 9 — adds RAG and session tables.

Revision ID: 002
Revises: 001
Create Date: 2026-06-05
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rag_document",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_uri", sa.String(1024), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("domain", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rag_document_source_uri", "rag_document", ["source_uri"])
    op.create_index("ix_rag_document_domain", "rag_document", ["domain"])

    op.create_table(
        "rag_chunk",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(36),
            sa.ForeignKey("rag_document.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("embedding", sa.LargeBinary, nullable=False),
        sa.Column("embedding_model", sa.String(128), nullable=False),
    )
    op.create_index("ix_rag_chunk_document_id", "rag_chunk", ["document_id"])

    op.create_table(
        "session",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agent_id", sa.String(255), nullable=False),
        sa.Column("goal", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_session_agent_id", "session", ["agent_id"])

    op.create_table(
        "message",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("session.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender", sa.String(255), nullable=False),
        sa.Column("receiver", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_message_session_id", "message", ["session_id"])


def downgrade() -> None:
    op.drop_table("message")
    op.drop_table("session")
    op.drop_table("rag_chunk")
    op.drop_table("rag_document")
```

### infrastructure/persistence/migrations/sql/versions/003_audit_event.py
```
"""Faza 11 — adds audit_event table.

Revision ID: 003
Revises: 002
Create Date: 2026-06-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_audit_event_type", "audit_event", ["event_type"])
    op.create_index("ix_audit_event_occurred_at", "audit_event", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_event_occurred_at", table_name="audit_event")
    op.drop_index("ix_audit_event_type", table_name="audit_event")
    op.drop_table("audit_event")
```

### infrastructure/persistence/migrations/sql/versions/004_outbox.py
```
"""Faza 12 — adds outbox_event table.

Revision ID: 004
Revises: 003
Create Date: 2026-06-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_outbox_event_type", "outbox_event", ["event_type"])
    op.create_index("ix_outbox_event_published_at", "outbox_event", ["published_at"])


def downgrade() -> None:
    op.drop_index("ix_outbox_event_published_at", table_name="outbox_event")
    op.drop_index("ix_outbox_event_type", table_name="outbox_event")
    op.drop_table("outbox_event")
```

### infrastructure/persistence/migrations/sql/versions/__init__.py
```
# alembic versions package
```

### infrastructure/persistence/mongo/__init__.py
```
```

### infrastructure/persistence/mongo/documents/__init__.py
```
```

### infrastructure/persistence/mongo/mappers/__init__.py
```
```

### infrastructure/persistence/mongo/repositories/__init__.py
```
```

### infrastructure/persistence/sql/__init__.py
```
"""SQL persistence — session factory and UnitOfWork."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_session_factory(url: str) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory for the given database URL.

    Supports both SQLite (sqlite+aiosqlite://...) and
    PostgreSQL (postgresql+asyncpg://...).
    """
    engine = create_async_engine(
        url,
        echo=False,
        future=True,
        # SQLite-specific: allow same connection across threads (needed by aiosqlite)
        connect_args={"check_same_thread": False} if "sqlite" in url else {},
    )
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_all_tables(url: str) -> None:
    """Create all tables (dev/test helper — production uses alembic)."""
    from shell_ddd.infrastructure.persistence.sql.models import Base

    engine = create_async_engine(url, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Async generator yielding a single AsyncSession (for use with Depends)."""
    async with session_factory() as session:
        yield session
```

### infrastructure/persistence/sql/mappers/__init__.py
```
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
```

### infrastructure/persistence/sql/models/__init__.py
```
"""SQLAlchemy 2.x ORM models — shared between SQLite and PostgreSQL."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TaskModel(Base):
    __tablename__ = "task"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_yaml_raw: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    graph: Mapped[GraphModel | None] = relationship(
        "GraphModel", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )


class GraphModel(Base):
    __tablename__ = "graph"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_dict: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]

    task: Mapped[TaskModel] = relationship("TaskModel", back_populates="graph")
    nodes: Mapped[list[GraphNodeModel]] = relationship(
        "GraphNodeModel", back_populates="graph", cascade="all, delete-orphan"
    )


class GraphNodeModel(Base):
    __tablename__ = "graph_node"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    graph_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("graph.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    node_dir: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    node_type: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    command: Mapped[str] = mapped_column(Text, nullable=False, default="")
    timeout: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    log_level: Mapped[str] = mapped_column(String(16), nullable=False, default="INFO")
    max_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    no_ask_user: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    autopilot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    source_dir: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    work_dir: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    status_initial: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    extra: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]

    graph: Mapped[GraphModel] = relationship("GraphModel", back_populates="nodes")


class WorkflowModel(Base):
    __tablename__ = "workflow"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    node_states: Mapped[list[NodeStateModel]] = relationship(
        "NodeStateModel", back_populates="workflow", cascade="all, delete-orphan"
    )


class NodeStateModel(Base):
    __tablename__ = "node_state"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflow.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle")
    step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    workflow: Mapped[WorkflowModel] = relationship("WorkflowModel", back_populates="node_states")


class EnvelopeModel(Base):
    __tablename__ = "envelope"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    sender_node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    receiver_node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_role: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    target_role: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    sequence_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    artifact_uri: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    archive_uri: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    events: Mapped[list[EnvelopeEventModel]] = relationship(
        "EnvelopeEventModel", back_populates="envelope", cascade="all, delete-orphan"
    )


class EnvelopeEventModel(Base):
    __tablename__ = "envelope_event"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    envelope_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("envelope.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    envelope: Mapped[EnvelopeModel] = relationship("EnvelopeModel", back_populates="events")


class PromptModel(Base):
    __tablename__ = "prompt"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_uri: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class NodeResultModel(Base):
    __tablename__ = "node_result"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    node_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    workflow_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    stdout: Mapped[str] = mapped_column(Text, nullable=False, default="")
    stderr: Mapped[str] = mapped_column(Text, nullable=False, default="")
    artifact_uri: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunnerConfigModel(Base):
    __tablename__ = "runner_config"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    package_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RagDocumentModel(Base):
    __tablename__ = "rag_document"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_uri: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    domain: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    chunks: Mapped[list[RagChunkModel]] = relationship(
        "RagChunkModel", back_populates="document", cascade="all, delete-orphan"
    )


class RagChunkModel(Base):
    __tablename__ = "rag_chunk"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rag_document.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)

    document: Mapped[RagDocumentModel] = relationship("RagDocumentModel", back_populates="chunks")


class SessionModel(Base):
    __tablename__ = "session"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    messages: Mapped[list[MessageModel]] = relationship(
        "MessageModel", back_populates="session", cascade="all, delete-orphan"
    )


class MessageModel(Base):
    __tablename__ = "message"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    receiver: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="messages")


class AuditEventModel(Base):
    __tablename__ = "audit_event"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]


class OutboxEventModel(Base):
    __tablename__ = "outbox_event"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

### infrastructure/persistence/sql/repositories/__init__.py
```
"""SQL repository adapters (SQLite + PostgreSQL via SQLAlchemy 2.x async)."""
from __future__ import annotations

import struct

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shell_ddd.domain.entities.envelope import Envelope
from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.entities.prompt import Prompt
from shell_ddd.domain.entities.rag_document import RagChunk, RagDocument
from shell_ddd.domain.entities.runner_config import RunnerConfig
from shell_ddd.domain.entities.session import Message, Session
from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.services.rag_index_service import cosine_similarity
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
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.persistence.sql.mappers import (  # noqa: E501
    envelope_entity_to_model,
    envelope_model_to_entity,
    node_result_entity_to_model,
    node_result_model_to_entity,
    prompt_entity_to_model,
    prompt_model_to_entity,
    runner_config_entity_to_model,
    runner_config_model_to_entity,
    task_entity_to_model,
    task_model_to_entity,
    workflow_entity_to_model,
    workflow_model_to_entity,
)
from shell_ddd.infrastructure.persistence.sql.models import (
    EnvelopeModel,
    MessageModel,
    NodeResultModel,
    PromptModel,
    RagChunkModel,
    RagDocumentModel,
    RunnerConfigModel,
    SessionModel,
    TaskModel,
    WorkflowModel,
)


class SqlTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, task_id: TaskId) -> Task | None:
        q = (
            select(TaskModel)
            .options(selectinload(TaskModel.graph))
            .where(TaskModel.id == task_id.value)
        )
        row = (await self._s.execute(q)).scalar_one_or_none()
        return task_model_to_entity(row) if row else None

    async def get_by_name(self, name: TaskName) -> Task | None:
        q = (
            select(TaskModel)
            .options(selectinload(TaskModel.graph))
            .where(TaskModel.name == name.value)
            .order_by(TaskModel.version.desc())
            .limit(1)
        )
        row = (await self._s.execute(q)).scalar_one_or_none()
        return task_model_to_entity(row) if row else None

    async def get_current_by_name(self, name: TaskName) -> Task | None:
        q = (
            select(TaskModel)
            .options(selectinload(TaskModel.graph))
            .where(TaskModel.name == name.value, TaskModel.is_current.is_(True))
            .limit(1)
        )
        row = (await self._s.execute(q)).scalar_one_or_none()
        return task_model_to_entity(row) if row else None

    async def save(self, task: Task) -> None:
        model = task_entity_to_model(task)
        await self._s.merge(model)

    async def list_current(self) -> list[Task]:
        q = (
            select(TaskModel)
            .options(selectinload(TaskModel.graph))
            .where(TaskModel.is_current.is_(True))
        )
        rows = (await self._s.execute(q)).scalars().all()
        return [task_model_to_entity(r) for r in rows]


class SqlWorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        q = (
            select(WorkflowModel)
            .options(selectinload(WorkflowModel.node_states))
            .where(WorkflowModel.id == workflow_id.value)
        )
        row = (await self._s.execute(q)).scalar_one_or_none()
        return workflow_model_to_entity(row) if row else None

    async def save(self, workflow: Workflow) -> None:
        # Delete existing node_states to avoid conflicts, then merge
        await self._s.execute(
            update(WorkflowModel)
            .where(WorkflowModel.id == workflow.id.value)
            .values(status=workflow.status.value)
        )
        model = workflow_entity_to_model(workflow)
        await self._s.merge(model)


class SqlEnvelopeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None:
        q = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(EnvelopeModel.id == envelope_id.value)
        )
        row = (await self._s.execute(q)).scalar_one_or_none()
        return envelope_model_to_entity(row) if row else None

    async def save(self, envelope: Envelope) -> None:
        model = envelope_entity_to_model(envelope)
        await self._s.merge(model)

    async def list_by_workflow(self, workflow_id: WorkflowId) -> list[Envelope]:
        q = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(EnvelopeModel.workflow_id == workflow_id.value)
        )
        rows = (await self._s.execute(q)).scalars().all()
        return [envelope_model_to_entity(r) for r in rows]

    async def list_pending(self, workflow_id: WorkflowId) -> list[Envelope]:
        q = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(
                EnvelopeModel.workflow_id == workflow_id.value,
                EnvelopeModel.status == EnvelopeStatus.PENDING.value,
            )
        )
        rows = (await self._s.execute(q)).scalars().all()
        return [envelope_model_to_entity(r) for r in rows]


class SqlPromptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, prompt_id: PromptId) -> Prompt | None:
        q = select(PromptModel).where(PromptModel.id == prompt_id.value)
        row = (await self._s.execute(q)).scalar_one_or_none()
        return prompt_model_to_entity(row) if row else None

    async def get_current_by_name(self, name: str) -> Prompt | None:
        q = select(PromptModel).where(
            PromptModel.name == name, PromptModel.is_current.is_(True)
        )
        row = (await self._s.execute(q)).scalar_one_or_none()
        return prompt_model_to_entity(row) if row else None

    async def save(self, prompt: Prompt) -> None:
        model = prompt_entity_to_model(prompt)
        await self._s.merge(model)


class SqlNodeResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, result_id: NodeResultId) -> NodeResult | None:
        q = select(NodeResultModel).where(NodeResultModel.id == result_id.value)
        row = (await self._s.execute(q)).scalar_one_or_none()
        return node_result_model_to_entity(row) if row else None

    async def get_by_node_and_workflow(
        self, node_id: NodeId, workflow_id: WorkflowId
    ) -> NodeResult | None:
        q = select(NodeResultModel).where(
            NodeResultModel.node_id == node_id.value,
            NodeResultModel.workflow_id == workflow_id.value,
        )
        row = (await self._s.execute(q)).scalar_one_or_none()
        return node_result_model_to_entity(row) if row else None

    async def save(self, result: NodeResult) -> None:
        model = node_result_entity_to_model(result)
        await self._s.merge(model)


class SqlRunnerConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None:
        q = select(RunnerConfigModel).where(RunnerConfigModel.id == config_id.value)
        row = (await self._s.execute(q)).scalar_one_or_none()
        return runner_config_model_to_entity(row) if row else None

    async def get_by_package(self, package_name: str) -> RunnerConfig | None:
        q = select(RunnerConfigModel).where(
            RunnerConfigModel.package_name == package_name
        )
        row = (await self._s.execute(q)).scalar_one_or_none()
        return runner_config_model_to_entity(row) if row else None

    async def save(self, config: RunnerConfig) -> None:
        model = runner_config_entity_to_model(config)
        await self._s.merge(model)


# ---------------------------------------------------------------------------
# No-op EnvelopeArchive (SQL stub — FS implementation in infrastructure/filesystem)
# ---------------------------------------------------------------------------


class SqlEnvelopeArchiveStub:
    """Stub — archives are stored on filesystem; this is a no-op SQL adapter."""

    async def archive(self, envelope: Envelope) -> str:
        return f"sql://archive/{envelope.id.value}"

    async def get(self, archive_uri: str) -> Envelope | None:
        return None


# ---------------------------------------------------------------------------
# RAG
# ---------------------------------------------------------------------------


class SqlRagDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, document: RagDocument) -> None:
        doc_model = RagDocumentModel(
            id=document.id.value,
            source_uri=document.source_uri,
            title=document.title,
            domain=document.domain,
            created_at=document.created_at,
        )
        await self._s.merge(doc_model)
        # delete+re-insert chunks to keep them consistent
        from sqlalchemy import delete as sa_delete
        await self._s.execute(
            sa_delete(RagChunkModel).where(RagChunkModel.document_id == document.id.value)
        )
        for chunk in document.chunks:
            self._s.add(
                RagChunkModel(
                    id=chunk.id.value,
                    document_id=chunk.document_id.value,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    embedding=chunk.embedding,
                    embedding_model=chunk.embedding_model,
                )
            )

    async def get_by_id(self, doc_id: RagDocumentId) -> RagDocument | None:
        q = (
            select(RagDocumentModel)
            .options(selectinload(RagDocumentModel.chunks))
            .where(RagDocumentModel.id == doc_id.value)
        )
        row = (await self._s.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        doc = RagDocument(
            id=RagDocumentId(row.id),
            source_uri=row.source_uri,
            title=row.title,
            domain=row.domain,
            created_at=row.created_at,
        )
        for c in sorted(row.chunks, key=lambda x: x.chunk_index):
            doc.chunks.append(
                RagChunk(
                    id=RagChunkId(c.id),
                    document_id=RagDocumentId(c.document_id),
                    chunk_index=c.chunk_index,
                    chunk_text=c.chunk_text,
                    embedding=c.embedding,
                    embedding_model=c.embedding_model,
                )
            )
        return doc

    async def search_similar(
        self,
        query_embedding: bytes,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RagChunk]:
        """Cosine-similarity brute-force search (SQLite-compatible)."""
        q = select(RagChunkModel).options(selectinload(RagChunkModel.document))
        if domain:
            q = q.join(RagDocumentModel).where(RagDocumentModel.domain == domain)
        rows = (await self._s.execute(q)).scalars().all()
        if not rows:
            return []
        dim = len(query_embedding) // 4
        query_vec = list(struct.unpack(f"{dim}f", query_embedding))
        scored: list[tuple[float, RagChunkModel]] = []
        for row in rows:
            chunk_vec = list(struct.unpack(f"{len(row.embedding) // 4}f", row.embedding))
            score = cosine_similarity(query_vec, chunk_vec)
            scored.append((score, row))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [
            RagChunk(
                id=RagChunkId(r.id),
                document_id=RagDocumentId(r.document_id),
                chunk_index=r.chunk_index,
                chunk_text=r.chunk_text,
                embedding=r.embedding,
                embedding_model=r.embedding_model,
            )
            for _, r in scored[:top_k]
        ]


# ---------------------------------------------------------------------------
# Session / Message
# ---------------------------------------------------------------------------


class SqlSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, entity: Session) -> None:
        model = SessionModel(
            id=entity.id.value,
            agent_id=entity.agent_id,
            goal=entity.goal,
            status=entity.status,
            opened_at=entity.opened_at,
            closed_at=entity.closed_at,
        )
        await self._s.merge(model)
        for msg in entity.messages:
            await self._s.merge(
                MessageModel(
                    id=msg.id.value,
                    session_id=msg.session_id.value,
                    sender=msg.sender,
                    receiver=msg.receiver,
                    payload=msg.payload,
                    created_at=msg.created_at,
                )
            )

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        q = select(SessionModel).where(SessionModel.id == session_id.value)
        row = (await self._s.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        return Session(
            id=SessionId(row.id),
            agent_id=row.agent_id,
            goal=row.goal,
            status=row.status,
            opened_at=row.opened_at,
            closed_at=row.closed_at,
        )

    async def get_messages(self, session_id: SessionId) -> list[Message]:
        q = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id.value)
            .order_by(MessageModel.created_at)
        )
        rows = (await self._s.execute(q)).scalars().all()
        return [
            Message(
                id=MessageId(r.id),
                session_id=SessionId(r.session_id),
                sender=r.sender,
                receiver=r.receiver,
                payload=r.payload,
                created_at=r.created_at,
            )
            for r in rows
        ]
```

### infrastructure/process/__init__.py
```
```

### infrastructure/process/command_builder.py
```
"""CommandBuilder — builds subprocess argv per node execution mode."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.manifest import Manifest

# Directory names inside .node/
_DOT_NODE = ".node"
DIR_OUTPUT = "output"
DIR_LOGS = "logs"
DIR_INPUT = "input"
DIR_TEMP = "temp"


def build_agent_command(
    manifest: Manifest,
    workspace_path: str,
    prompt: str = "",
    model: str = "",
    extra_add_dirs: list[str] | None = None,
) -> list[str]:
    """Build argv for running the `copilot` agent binary."""
    import shutil

    binary = shutil.which("copilot")
    if binary is None:
        raise FileNotFoundError(
            "copilot binary not found on PATH. Install GitHub Copilot CLI."
        )

    cmd: list[str] = []

    # On Windows .cmd/.bat wrappers need to be invoked via cmd /c
    import os

    if os.name == "nt" and binary.lower().endswith((".cmd", ".bat")):
        cmd += ["cmd", "/c", binary]
    else:
        cmd.append(binary)

    if model:
        cmd += ["--model", model]

    import pathlib

    ws = pathlib.Path(workspace_path)
    output_dir = ws / _DOT_NODE / DIR_OUTPUT
    logs_dir = ws / _DOT_NODE / DIR_LOGS

    cmd += ["--add-dir", str(output_dir)]
    if extra_add_dirs:
        for d in extra_add_dirs:
            cmd += ["--add-dir", d]
    cmd += ["--add-dir", str(ws)]
    cmd += ["--log-dir", str(logs_dir)]

    return cmd


def build_sub_node_command(
    entrypoint_path: str,
    node_dir: str,
    source_dir: str,
    work_dir: str,
    task_name: str,
    task_dir: str,
    mode: str = "",
    model: str = "",
    role: str = "",
    parent_node_dir: str = "",
    parent_thread_id: str = "",
    python_exe: str | None = None,
) -> list[str]:
    """Build argv for running a sub-node entrypoint (used by tasker)."""
    exe = python_exe or sys.executable
    cmd = [exe, entrypoint_path]
    cmd += ["--node-dir", node_dir]
    cmd += ["--source-dir", source_dir]
    cmd += ["--work-dir", work_dir]
    cmd += ["--task-name", task_name]
    cmd += ["--task-dir", task_dir]
    if parent_node_dir:
        cmd += ["--parent-node-dir", parent_node_dir]
    if parent_thread_id:
        cmd += ["--parent-thread-id", parent_thread_id]
    if mode == "agent" and model:
        cmd += ["--model", model]
    if role:
        cmd += ["--role", role]
    return cmd
```

### infrastructure/process/subprocess_runner.py
```
"""SubprocessNodeProcessRunner — real NodeProcessRunner adapter using asyncio subprocess."""
from __future__ import annotations

import asyncio
import os
import pathlib
import sys
from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.execution_result import ExecutionResult

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.manifest import Manifest

# Modes that use the shell_ddd framework CLI entrypoint (not an external binary).
_FRAMEWORK_MODES = {"router", "tasker", "tool", "worker", "agent"}

# Path to shell_ddd/framework/entrypoints/ (resolved relative to this file).
_ENTRYPOINTS_DIR = pathlib.Path(__file__).parent.parent.parent / "framework" / "entrypoints"


class SubprocessNodeProcessRunner:
    """Runs a node subprocess using asyncio.create_subprocess_exec.

    Mode routing:
    - ``agent`` → ``copilot`` binary via ``build_agent_command``
    - ``router | tasker | tool | worker`` → Python + framework entrypoint via
      ``build_sub_node_command``
    """

    DEFAULT_TIMEOUT_SECONDS = 300

    async def run(
        self,
        manifest: Manifest,
        workspace_path: str,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult:
        """Execute the node and return stdout/stderr/returncode."""
        mode = str(manifest.mode)
        run_env = {**os.environ, "PYTHONUTF8": "1"}
        if env:
            run_env.update(env)

        if mode == "agent":
            from shell_ddd.infrastructure.process.command_builder import build_agent_command

            argv = build_agent_command(
                manifest,
                workspace_path,
                model=getattr(manifest, "model", ""),
            )
        elif mode in _FRAMEWORK_MODES:
            argv = self._build_framework_argv(manifest, workspace_path, env or {})
        else:
            # Unknown mode — try executing manifest.name as a direct executable (fallback).
            argv = [manifest.name]

        return await self._run_argv(argv, workspace_path, run_env)

    # ------------------------------------------------------------------

    def _build_framework_argv(
        self,
        manifest: Manifest,
        workspace_path: str,
        env: dict[str, str],
    ) -> list[str]:
        """Return argv for running a sub-node via the framework entrypoint."""
        from shell_ddd.infrastructure.process.command_builder import build_sub_node_command

        mode = str(manifest.mode)
        entrypoint = str(_ENTRYPOINTS_DIR / f"{mode}_entrypoint.py")
        workflow_id = env.get("SHELL_DDD_WORKFLOW_ID", "")
        task_name = env.get("SHELL_DDD_TASK_NAME", "")

        return build_sub_node_command(
            entrypoint_path=entrypoint,
            node_dir=workspace_path,
            source_dir=workspace_path,
            work_dir=workspace_path,
            task_name=task_name,
            task_dir=workspace_path,
            mode=mode,
            role=manifest.role,
            python_exe=sys.executable,
        )

    async def _run_argv(
        self,
        argv: list[str],
        cwd: str,
        env: dict[str, str],
        stdin_data: str = "",
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> ExecutionResult:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            cwd=cwd,
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdin_bytes = stdin_data.encode("utf-8") if stdin_data else None
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(input=stdin_bytes),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr=f"Process timed out after {timeout}s",
            )

        return ExecutionResult(
            returncode=proc.returncode if proc.returncode is not None else -1,
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
        )


    async def _run_argv(
        self,
        argv: list[str],
        cwd: str,
        env: dict[str, str],
        stdin_data: str = "",
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> ExecutionResult:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            cwd=cwd,
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdin_bytes = stdin_data.encode("utf-8") if stdin_data else None
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(input=stdin_bytes),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr=f"Process timed out after {timeout}s",
            )

        return ExecutionResult(
            returncode=proc.returncode if proc.returncode is not None else -1,
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
        )
```

### infrastructure/time/__init__.py
```
"""System clock and UUID-based ID generator."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from shell_ddd.domain.value_objects.ids import (
    EnvelopeId,
    NodeResultId,
    PromptId,
    RunnerConfigId,
    TaskId,
    WorkflowId,
)


class SystemClock:
    """Real wall-clock implementation of Clock port."""

    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)


class UuidIdGenerator:
    """UUID4-based implementation of IdGenerator port."""

    def new_task_id(self) -> TaskId:
        return TaskId(str(uuid.uuid4()))

    def new_workflow_id(self) -> WorkflowId:
        return WorkflowId(str(uuid.uuid4()))

    def new_envelope_id(self) -> EnvelopeId:
        return EnvelopeId(str(uuid.uuid4()))

    def new_prompt_id(self) -> PromptId:
        return PromptId(str(uuid.uuid4()))

    def new_node_result_id(self) -> NodeResultId:
        return NodeResultId(str(uuid.uuid4()))

    def new_runner_config_id(self) -> RunnerConfigId:
        return RunnerConfigId(str(uuid.uuid4()))
```

### infrastructure/time/system_clock.py
```
"""SystemClock — real wall-clock implementation of the Clock port."""
from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(tz=UTC)
```

### README.md
```
# shell_ddd — Przewodnik po projekcie

`shell_ddd` to reimplementacja platformy SHELL w architekturze DDD + Hexagonal + CQRS.  
Stary katalog `shell/` pozostaje niezmieniony i służy jako referencja behawioralna.

---

## Spis treści

1. [Instalacja i wymagania](#1-instalacja-i-wymagania)
2. [Zmienne środowiskowe](#2-zmienne-środowiskowe)
3. [Uruchamianie — CLI](#3-uruchamianie--cli)
4. [Uruchamianie — FastAPI](#4-uruchamianie--fastapi)
5. [Narzędzia administracyjne (bootstrap/main.py)](#5-narzędzia-administracyjne-bootstrapMainpy)
6. [Testowanie](#6-testowanie)
7. [Architektura warstwowa](#7-architektura-warstwowa)
8. [Mapa plików — co gdzie jest](#8-mapa-plików--co-gdzie-jest)
9. [Agregaty i ich relacje](#9-agregaty-i-ich-relacje)
10. [Szyny (CommandBus / QueryBus / EventBus)](#10-szyny)
11. [Persistence — adaptery bazodanowe](#11-persistence--adaptery-bazodanowe)
12. [Observability](#12-observability)

---

## 1. Instalacja i wymagania

**Python 3.11+** wymagany.

```powershell
# z katalogu głównego repo (SHELL/)
pip install -e "shell_ddd[dev]"
```

Zależności produkcyjne (z `shell_ddd/pyproject.toml`):

| Pakiet | Do czego |
|---|---|
| `fastapi`, `uvicorn` | REST API (control plane) |
| `sqlalchemy>=2.0` | ORM async (SQLite + Postgres) |
| `aiosqlite` | SQLite async driver |
| `asyncpg` | PostgreSQL async driver |
| `alembic` | Migracje schematu SQL |
| `pydantic>=2.7`, `pydantic-settings` | DTO, Settings, request/response modele |
| `motor` | MongoDB async driver (adapter zawieszony) |
| `pyyaml` | Parsowanie task.yaml |
| `httpx` | Klient HTTP w testach e2e |

Zależności dev (`[dev]`): `pytest`, `pytest-asyncio`, `pytest-cov`, `mypy`, `ruff`.

---

## 2. Zmienne środowiskowe

Wszystkie mają wartości domyślne — projekt działa bez ustawiania czegokolwiek.

| Zmienna | Domyślna wartość | Opis |
|---|---|---|
| `SHELL_DDD_DATABASE_URL` | `sqlite+aiosqlite:///shell_ddd.db` | URL bazy danych; zmień na `postgresql+asyncpg://...` dla Postgres |
| `SHELL_DDD_MAX_STEP` | `20` | Maksymalna liczba kroków routingu w jednym przebiegu |
| `SHELL_DDD_MAX_PARALLEL` | `4` | Liczba równoległych node'ów w `run-tasker` |
| `PG_TEST_URL` | *(brak)* | URL Postgres dla testów integracyjnych; testy są pomijane gdy nie ustawione |

Ustawianie w PowerShell (tymczasowo na czas sesji):

```powershell
$env:SHELL_DDD_DATABASE_URL = "sqlite+aiosqlite:///moja_baza.db"
$env:SHELL_DDD_MAX_STEP = "50"
```

Ustawianie dla Postgres:

```powershell
$env:SHELL_DDD_DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/shell"
```

---

## 3. Uruchamianie — CLI

Wszystkie komendy uruchamiane z **katalogu głównego repo** (`SHELL/`):

```powershell
python -m shell_ddd.framework.cli.main <subkomenda> [parametry]
```

### 3.1 `import-task` — importuj zadanie z pliku

Czyta parę plików `<task-name>.md` + `<task-name>.yaml` i zapisuje `Task` do bazy.

```powershell
python -m shell_ddd.framework.cli.main import-task `
    --task-name my-task `
    --task-dir ./workplace/example_tasks/
```

| Parametr | Wymagany | Opis |
|---|---|---|
| `--task-name NAME` | tak | Nazwa zadania (bez rozszerzenia); szuka `<task-dir>/<NAME>.md` i `.yaml` |
| `--task-dir PATH` | tak | Katalog z plikami `.md` i `.yaml` |

Wynik: wypisuje `Imported task 'my-task' with id=<uuid>`.

---

### 3.2 `route` — uruchom routing workflow

Przetwarza oczekujące koperty (`Envelope`) dla danego workflow.

```powershell
python -m shell_ddd.framework.cli.main route `
    --workflow-id <uuid>
```

| Parametr | Wymagany | Opis |
|---|---|---|
| `--workflow-id ID` | nie | UUID workflow; domyślnie `"default"` |
| `--max-step N` | nie | Nadpisuje `SHELL_DDD_MAX_STEP` |

Wynik: `Routed N envelopes.`

---

### 3.3 `run-tasker` — pełny cykl orchestracji

Importuje zadanie (jeśli nie istnieje), uruchamia workflow i wykonuje wszystkie node'y w grafie.

```powershell
python -m shell_ddd.framework.cli.main run-tasker `
    --task-name my-task `
    --work-dir ./work/
```

| Parametr | Wymagany | Opis |
|---|---|---|
| `--task-name NAME` | tak | Nazwa zaimportowanego zadania |
| `--work-dir PATH` | nie | Katalog roboczy node'ów; domyślnie CWD |

Wynik: `Tasker workflow completed: workflow_id=<uuid>`

---

### 3.4 `agent` / `router` / `tasker` / `tool` / `worker` — uruchamianie pojedynczego node'a

Wywołania odpowiadające starym entrypointom (CLI parity):

```powershell
python -m shell_ddd.framework.cli.main agent `
    --node-dir ./work/agent-01 `
    --workflow-id <uuid> `
    --work-dir ./work/
```

Wszystkie tryby przyjmują ten sam zestaw flag (zdefiniowany w `framework/cli/parser.py`):

| Parametr | Opis |
|---|---|
| `--node-dir PATH` | Katalog konkretnego node'a |
| `--workflow-id ID` | UUID workflow |
| `--work-dir PATH` | Katalog roboczy |
| `--max-step N` | Max kroków routingu |
| `--mode MODE` | Tryb wykonania (agent/router/tasker/tool/worker) |
| `--role ROLE` | Rola node'a |
| `--model MODEL` | Model LLM |
| `--timeout SECONDS` | Timeout wykonania |
| `--dry-run` | Symulacja bez zapisu |
| `--log-level LEVEL` | `DEBUG`/`INFO`/`WARNING`/`ERROR` (domyślnie `INFO`) |
| `--prompt PROMPT` | Treść promptu |
| `--prompt-dir PATH` | Katalog z plikami promptów |
| `--autopilot` | Tryb autopilota (bez pytania użytkownika) |
| `--no-ask-user` | Wyłącza interakcję z użytkownikiem |
| `--add-dir PATH` | Dodatkowy katalog (można podać wielokrotnie) |

---

## 4. Uruchamianie — FastAPI

FastAPI to **control plane** — zarządzanie taskami i workflow przez HTTP.  
Nie zastępuje CLI dla wykonania node'ów; działa równolegle.

### Uruchomienie serwera

```powershell
# Najpierw zainicjuj kontener i podaj go do create_app
python -c "
import asyncio, uvicorn
from shell_ddd.bootstrap.container import ApplicationFactory
from shell_ddd.framework.api.app import create_app

async def main():
    container = await ApplicationFactory(database_url='sqlite+aiosqlite:///shell_ddd.db').build()
    app = create_app(container)
    config = uvicorn.Config(app, host='0.0.0.0', port=8000)
    server = uvicorn.Server(config)
    await server.serve()

asyncio.run(main())
"
```

### Endpointy

Dokumentacja Swagger dostępna pod: `http://localhost:8000/docs`

| Metoda | Ścieżka | Opis |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/tasks/import` | Import zadania |
| `GET` | `/tasks/{name}` | Pobierz task po nazwie |
| `POST` | `/workflows` | Utwórz nowy workflow |
| `GET` | `/workflows/{id}` | Pobierz status workflow |
| `POST` | `/workflows/{id}/route` | Uruchom routing |
| `GET` | `/workflows/{id}/envelopes` | Lista kopert workflow |
| `GET` | `/nodes/{id}/result` | Wynik wykonania node'a |

### Przykłady curl

```bash
# Import zadania
curl -X POST http://localhost:8000/tasks/import \
  -H "Content-Type: application/json" \
  -d '{"task_name":"my-task","md_path":"/path/to/my-task.md","yaml_path":"/path/to/my-task.yaml"}'

# Utwórz workflow
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{"task_name":"my-task"}'

# Sprawdź status
curl http://localhost:8000/workflows/<workflow_id>

# Uruchom routing
curl -X POST http://localhost:8000/workflows/<workflow_id>/route
```

Każde żądanie dostaje nagłówek `X-Correlation-Id` (generowany automatycznie lub przekazany przez klienta).

---

## 5. Narzędzia administracyjne (bootstrap/main.py)

```powershell
python -m shell_ddd.bootstrap.main <komenda> [--db-url URL]
```

| Komenda | Opis |
|---|---|
| `smoke` | Import → workflow → route na tymczasowej bazie SQLite. Sprawdza czy cały stos działa. |
| `relay` | Przetwarza jeden batch oczekujących wpisów w tabeli `outbox_event` i publikuje je downstream. |

```powershell
# Smoke test na domyślnej bazie
python -m shell_ddd.bootstrap.main smoke

# Smoke test na konkretnej bazie
python -m shell_ddd.bootstrap.main smoke --db-url sqlite+aiosqlite:///moja_baza.db

# Przetworz outbox na bazie Postgres
python -m shell_ddd.bootstrap.main relay --db-url "postgresql+asyncpg://user:pass@localhost/shell"
```

---

## 6. Testowanie

### Uruchamianie testów

```powershell
# Wszystkie testy (z katalogu SHELL/)
python -m pytest shell_ddd/tests -x

# Tylko unit testy (szybkie, bez I/O)
python -m pytest shell_ddd/tests/unit -x

# Tylko integracyjne SQLite
python -m pytest shell_ddd/tests/integration/sql_sqlite -x

# Integracyjne Postgres (wymaga uruchomionego kontenera)
docker compose -f shell_ddd/docker-compose.test.yml up -d postgres
$env:PG_TEST_URL = "postgresql+asyncpg://shell:shell@localhost:5432/shell_test"
python -m pytest shell_ddd/tests/integration/sql_postgres -x
docker compose -f shell_ddd/docker-compose.test.yml down -v

# Testy e2e CLI
python -m pytest shell_ddd/tests/e2e/cli -x

# Testy e2e API (FastAPI TestClient)
python -m pytest shell_ddd/tests/e2e/api -x

# Architektura (sprawdza zakazy importów między warstwami)
python -m pytest shell_ddd/tests/architecture -x

# Z pokryciem kodu
python -m pytest shell_ddd/tests --cov=shell_ddd --cov-report=term-missing
```

### Flagi pytest

| Flaga | Opis |
|---|---|
| `-x` | Zatrzymaj po pierwszym błędzie |
| `-v` | Tryb verbose (lista wszystkich testów) |
| `-q` | Tryb cichy (tylko podsumowanie) |
| `--tb=short` | Krótki traceback (domyślnie `short`) |
| `-k "słowo"` | Uruchom tylko testy pasujące do wyrażenia, np. `-k "task"` |
| `--no-header` | Bez nagłówka pytest |

### Lint i typy

```powershell
# Ruff — linter (całe shell_ddd)
python -m ruff check shell_ddd

# Ruff z auto-fixem
python -m ruff check shell_ddd --fix

# MyPy — strict dla domain i application
python -m mypy --strict shell_ddd/domain shell_ddd/application

# MyPy bez strict dla reszty
python -m mypy shell_ddd/infrastructure shell_ddd/framework shell_ddd/bootstrap
```

### Struktura testów i co gdzie pisać

```
shell_ddd/tests/
├── architecture/
│   └── test_imports.py          ← AST scanner: zakazy importów między warstwami
├── unit/
│   ├── domain/                  ← Testy encji, VO, serwisów domenowych — bez I/O, bez mocków portów
│   └── application/             ← Handlery z InMemory* adapterami i Fake* portami
│       ├── test_import_task.py
│       ├── test_workflow.py
│       ├── test_logging_publishers.py
│       └── test_outbox.py
├── integration/
│   ├── sql_sqlite/
│   │   └── __init__.py          ← Testy repozytoriów i UoW przez prawdziwe SQLite (aiosqlite)
│   ├── sql_postgres/
│   │   └── __init__.py          ← Jak wyżej, ale Postgres — pomijane gdy brak PG_TEST_URL
│   └── filesystem/              ← Operacje FS z tmp_path
├── e2e/
│   ├── cli/
│   │   └── test_tasker_full_graph.py   ← Pełne cykle orkiestracji przez CLI
│   └── api/
│       └── test_api.py          ← FastAPI TestClient: HTTP → CommandBus → DB
```

**Wzorzec unit testu handlera** (korzysta z InMemory adapterów):

```python
async def test_import_task_saves_to_repo() -> None:
    from shell_ddd.application.command_handlers.import_task_handler import ImportTaskHandler
    from shell_ddd.application.commands.commands import ImportTaskCommand
    from shell_ddd.infrastructure.persistence.memory.memory import (
        InMemoryUnitOfWork, FakeClock, FakeIdGenerator, FakeEventPublisher, FakeTaskLoader,
    )

    uow = InMemoryUnitOfWork()
    handler = ImportTaskHandler(
        uow=uow,
        clock=FakeClock(),
        id_gen=FakeIdGenerator(),
        task_loader=FakeTaskLoader(body="# Test"),
        events=FakeEventPublisher(),
    )
    task_id = await handler.handle(ImportTaskCommand(md_path="t.md", yaml_path="t.yaml", task_name="t"))
    assert task_id is not None
```

---

## 7. Architektura warstwowa

```
domain ← application ← infrastructure ← framework ← bootstrap
```

Importy idą **tylko w tym kierunku** — żadna niższa warstwa nie może importować z wyższej.

| Warstwa | Co zawiera | Dozwolone importy |
|---|---|---|
| `domain/` | Encje, VO, porty repozytoriów, eventy domenowe, wyjątki | Tylko stdlib |
| `application/` | Komendy, zapytania, handlery, porty (Protocol), strategie | `domain/` + stdlib |
| `infrastructure/` | Adaptery SQL/Memory/FS/Process, logging, messaging | `domain/` + `application/` + libs |
| `framework/` | CLI (argparse) + FastAPI | `domain/` + `application/` + `infrastructure/` |
| `bootstrap/` | `ApplicationFactory` — składa wszystko razem | Wszystkie warstwy |
| `shared/` | `UuidIdGenerator` i inne pomocnicze | Tylko stdlib |

---

## 8. Mapa plików — co gdzie jest

### domain/

```
domain/
├── entities/
│   ├── task.py              Task, Graph, GraphNode
│   ├── workflow.py          Workflow, NodeState
│   ├── envelope.py          Envelope, EnvelopeEvent
│   ├── node_result.py       NodeResult
│   ├── prompt.py            Prompt
│   ├── runner_config.py     RunnerConfig
│   ├── rag_document.py      RagDocument, RagChunk
│   └── session.py           Session, Message
├── value_objects/
│   ├── ids.py               TaskId, WorkflowId, EnvelopeId, NodeId, ...
│   ├── task_name.py         TaskName
│   ├── status.py            Status (pending/running/done/failed)
│   ├── envelope_status.py   EnvelopeStatus
│   └── ...
├── repositories/            Porty (Protocol) — czyste interfejsy bez implementacji
│   ├── task_repository.py
│   ├── workflow_repository.py
│   └── ...
├── events/
│   └── events.py            TaskImported, WorkflowStarted, EnvelopeRouted, NodeCompleted, ...
├── services/
│   ├── graph_routing_service.py
│   └── rag_index_service.py
└── exceptions.py            DomainError i podklasy
```

### application/

```
application/
├── commands/
│   └── commands.py          Wszystkie Command dataclassy (frozen=True)
├── queries/
│   └── queries.py           Wszystkie Query dataclassy (frozen=True)
├── command_handlers/        Jeden handler per plik
│   ├── import_task_handler.py
│   ├── start_workflow_handler.py
│   ├── route_envelopes_handler.py
│   ├── run_node_handler.py
│   ├── run_tasker_workflow_handler.py
│   ├── save_node_result_handler.py
│   ├── save_prompt_handler.py
│   ├── archive_envelope_handler.py
│   └── bootstrap_runner_config_handler.py
├── query_handlers/
│   └── query_handlers.py    GetWorkflowHandler, GetTaskByNameHandler, ...
├── dto/                     DTO zwracane przez handlery zapytań
├── mappers/                 Entity ↔ DTO
├── ports/
│   └── ports.py             UnitOfWork, Clock, IdGenerator, EventPublisher, Logger, NodeProcessRunner, TaskLoader
├── strategies/
│   ├── node_execution_strategy.py   (Protocol)
│   ├── agent_strategy.py
│   ├── router_strategy.py
│   ├── tasker_strategy.py
│   ├── tool_strategy.py
│   └── worker_strategy.py
├── event_handlers/          Subskrybenci eventów domenowych
└── bus.py                   CommandBus, QueryBus, EventBus
```

### infrastructure/

```
infrastructure/
├── persistence/
│   ├── sql/
│   │   ├── __init__.py           build_session_factory(), create_all_tables()
│   │   ├── models/               SQLAlchemy ORM modele (TaskModel, WorkflowModel, ...)
│   │   ├── repositories/         SqlTaskRepository, SqlWorkflowRepository, ...
│   │   └── unit_of_work.py       SqlAlchemyUnitOfWork
│   ├── memory/
│   │   └── memory.py             InMemoryUnitOfWork, FakeClock, FakeIdGenerator, FakeEventPublisher, FakeTaskLoader
│   └── migrations/
│       └── sql/versions/
│           ├── 001_initial.py
│           ├── 002_rag_session.py
│           ├── 003_audit_event.py
│           └── 004_outbox.py
├── filesystem/
│   ├── task_loader.py            Czyta .md + .yaml z dysku → TaskBody
│   ├── node_workspace.py         Zarządza katalogiem roboczym node'a
│   └── envelope_archive_fs.py    FS-based archiwum kopert
├── process/
│   └── subprocess_runner.py      NodeProcessRunner — uruchamia node'y przez subprocess
├── logging/
│   ├── stdlib_logger.py          StdlibLogger (JSON output, correlation_id)
│   ├── logging_event_publisher.py
│   ├── sql_audit_publisher.py    Zapis do tabeli audit_event
│   └── composite_event_publisher.py
├── messaging/
│   ├── sql_outbox_publisher.py   Zapis do tabeli outbox_event
│   ├── memory_outbox_store.py    InMemory outbox (testy)
│   └── outbox_relay.py           Relay: czyta outbox → downstream publisher
├── rag/                          RAG repozytoria
└── configuration/                Settings (pydantic-settings)
```

### framework/

```
framework/
├── cli/
│   ├── main.py       Dispatcher: argv → subkomenda → asyncio.run(handler)
│   └── parser.py     build_parser() — wspólny argparse dla wszystkich trybów
└── api/
    ├── app.py                create_app(container) → FastAPI
    ├── routers/
    │   ├── tasks.py          POST /tasks/import, GET /tasks/{name}
    │   ├── workflows.py      POST /workflows, GET /workflows/{id}, POST /{id}/route
    │   ├── envelopes.py      GET /workflows/{id}/envelopes
    │   └── nodes.py          GET /nodes/{id}/result
    └── middleware/
        ├── correlation_id.py CorrelationIdMiddleware (X-Correlation-Id header)
        └── error_handler.py  DomainError → HTTP 4xx
```

### bootstrap/

```
bootstrap/
├── container.py   ApplicationFactory.build() → Container(command_bus, query_bus, event_bus)
└── main.py        python -m shell_ddd.bootstrap.main smoke|relay
```

---

## 9. Agregaty i ich relacje

```mermaid
graph TD
    Task -->|ma| Graph
    Graph -->|zawiera| GraphNode
    Workflow -->|śledzi| NodeState
    Workflow -->|powiązany z| Task
    Envelope -->|należy do| Workflow
    Envelope -->|dotyczy| GraphNode
    NodeResult -->|wynik| Envelope
    Prompt -->|używany przez| GraphNode
    RunnerConfig -->|konfiguruje| GraphNode
    RagDocument -->|zawiera| RagChunk
    Session -->|zawiera| Message
```

---

## 10. Szyny

### Rejestracja handlera

Wszystkie handlery są rejestrowane w `bootstrap/container.py`:

```python
command_bus.register(ImportTaskCommand, import_task_handler)
query_bus.register(GetWorkflowQuery, get_workflow_handler)
event_bus.subscribe(TaskImported, on_task_imported)
```

### Wywołanie z kodu

```python
# Command (zapis stanu)
task_id: TaskId = await container.command_bus.dispatch(
    ImportTaskCommand(md_path="...", yaml_path="...", task_name="...")
)

# Query (odczyt bez efektów ubocznych)
dto: WorkflowDto | None = await container.query_bus.dispatch(
    GetWorkflowQuery(workflow_id="<uuid>")
)
```

---

## 11. Persistence — adaptery bazodanowe

### Tabele SQL

| Tabela | Zawiera |
|---|---|
| `task` | Zadania (md_body, yaml_body, graph JSON) |
| `workflow` | Instancje workflow + status |
| `node_state` | Stan każdego node'a w workflow |
| `envelope` | Koperty routingu |
| `node_result` | Wyniki wykonania node'ów |
| `prompt` | Przechowywane prompty |
| `runner_config` | Konfiguracje runnerów |
| `rag_document` | Dokumenty RAG |
| `rag_chunk` | Chunki dokumentów RAG |
| `session` | Sesje konwersacji |
| `message` | Wiadomości w sesjach |
| `audit_event` | Logi eventów domenowych (append-only) |
| `outbox_event` | Transactional outbox (at-least-once delivery) |

### Migracje

Migracje są aplikowane automatycznie przy każdym `ApplicationFactory.build()` przez `create_all_tables()`.  
Pliki migracji: `infrastructure/persistence/migrations/sql/versions/`.

### Zmiana backendu

```powershell
# SQLite (domyślny, bez konfiguracji)
$env:SHELL_DDD_DATABASE_URL = "sqlite+aiosqlite:///shell_ddd.db"

# PostgreSQL
$env:SHELL_DDD_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/shell_db"
```

---

## 12. Observability

### Logi (JSON)

`StdlibLogger` wypisuje każdy log jako jednolinijkowy JSON na stdout:

```json
{"ts": "2025-01-15T10:23:45.123456", "level": "INFO", "logger": "shell_ddd", "msg": "domain_event", "event_type": "TaskImported", "correlation_id": "abc-123"}
```

Correlation ID jest propagowane przez `contextvars` — ustawiane automatycznie przez `CorrelationIdMiddleware` (API) lub można je ustawić ręcznie:

```python
from shell_ddd.infrastructure.logging.stdlib_logger import set_correlation_id
set_correlation_id("moj-request-id")
```

### Tabela audit_event

Każdy opublikowany event domenowy trafia do tabeli `audit_event` (przez `SqlAuditPublisher`).  
Kolumny: `id`, `event_type`, `occurred_at`, `payload` (JSON).

### Tabela outbox_event

`SqlOutboxPublisher` zapisuje eventy do `outbox_event` z `published_at = NULL`.  
`OutboxRelay.run_once()` pobiera niepublikowane wpisy i przekazuje je downstream, ustawiając `published_at`.

```powershell
# Uruchom relay ręcznie
python -m shell_ddd.bootstrap.main relay --db-url sqlite+aiosqlite:///shell_ddd.db
```
```

### shared/__init__.py
```
```

### shared/ids.py
```
"""Shared ID generators."""
from __future__ import annotations

import uuid

from shell_ddd.domain.value_objects.ids import (
    EnvelopeId,
    NodeResultId,
    PromptId,
    RunnerConfigId,
    TaskId,
    WorkflowId,
)


class UuidIdGenerator:
    """Generates real UUID-based IDs."""

    def new_task_id(self) -> TaskId:
        return TaskId(str(uuid.uuid4()))

    def new_workflow_id(self) -> WorkflowId:
        return WorkflowId(str(uuid.uuid4()))

    def new_envelope_id(self) -> EnvelopeId:
        return EnvelopeId(str(uuid.uuid4()))

    def new_prompt_id(self) -> PromptId:
        return PromptId(str(uuid.uuid4()))

    def new_node_result_id(self) -> NodeResultId:
        return NodeResultId(str(uuid.uuid4()))

    def new_runner_config_id(self) -> RunnerConfigId:
        return RunnerConfigId(str(uuid.uuid4()))
```

### tests/__init__.py
```
```

### tests/architecture/__init__.py
```
```

### tests/architecture/test_imports.py
```
"""Architecture test — verifies domain and application layer import rules.

Uses AST parsing (no imports executed) to check that:
- domain/ does not import from application/, infrastructure/, framework/, bootstrap/
- application/ does not import from infrastructure/, framework/, bootstrap/
"""
from __future__ import annotations

import ast
import pathlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

BASE = pathlib.Path(__file__).parent.parent.parent  # shell_ddd/


def _iter_python_files(layer: str) -> Iterator[pathlib.Path]:
    layer_path = BASE / layer
    if not layer_path.exists():
        return
    yield from layer_path.rglob("*.py")


def _get_imports(path: pathlib.Path) -> list[str]:
    """Return all imported module prefixes from a Python file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


_FORBIDDEN: dict[str, list[str]] = {
    "domain": [
        "shell_ddd.application",
        "shell_ddd.infrastructure",
        "shell_ddd.framework",
        "shell_ddd.bootstrap",
        "sqlalchemy",
        "pydantic",
        "fastapi",
        "motor",
    ],
    "application": [
        "shell_ddd.infrastructure",
        "shell_ddd.framework",
        "shell_ddd.bootstrap",
        "sqlalchemy",
        "fastapi",
        "motor",
    ],
}


def test_domain_layer_imports() -> None:
    violations: list[str] = []
    forbidden = _FORBIDDEN["domain"]
    for path in _iter_python_files("domain"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    violations.append(f"{path.relative_to(BASE)}: imports {imp!r}")
    assert not violations, "Domain layer import violations:\n" + "\n".join(violations)


def test_application_layer_imports() -> None:
    violations: list[str] = []
    forbidden = _FORBIDDEN["application"]
    for path in _iter_python_files("application"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    violations.append(f"{path.relative_to(BASE)}: imports {imp!r}")
    assert not violations, "Application layer import violations:\n" + "\n".join(violations)
```

### tests/conftest.py
```
"""Root conftest for shell_ddd tests.

Provides fixtures for all three persistence backends:
- InMemory (always available)
- SQLite (always available)
- PostgreSQL (skipped unless POSTGRES_TEST_URL env var set)
- MongoDB (skipped unless MONGO_TEST_URL env var set)
"""
from __future__ import annotations

import os

import pytest  # noqa: F401 — used in type annotations and fixtures

# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: integration tests requiring external services")
    config.addinivalue_line("markers", "e2e: end-to-end tests")


# ---------------------------------------------------------------------------
# Backend availability flags
# ---------------------------------------------------------------------------

POSTGRES_URL = os.environ.get(
    "POSTGRES_TEST_URL",
    "postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test",
)
MONGO_URL = os.environ.get("MONGO_TEST_URL", "mongodb://localhost:27018/?replicaSet=rs0")

_postgres_available = os.environ.get("POSTGRES_TEST_URL") is not None
_mongo_available = os.environ.get("MONGO_TEST_URL") is not None


# ---------------------------------------------------------------------------
# Skip helpers
# ---------------------------------------------------------------------------

skip_no_postgres = pytest.mark.skipif(
    not _postgres_available,
    reason="POSTGRES_TEST_URL not set — start docker-compose.test.yml to enable",
)

skip_no_mongo = pytest.mark.skipif(
    not _mongo_available,
    reason="MONGO_TEST_URL not set — start docker-compose.test.yml to enable",
)


# ---------------------------------------------------------------------------
# URL fixtures (for integration tests that need raw URLs)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def sqlite_test_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    return f"sqlite+aiosqlite:///{db_path}"


@pytest.fixture(scope="session")
def postgres_test_url() -> str:
    return POSTGRES_URL


@pytest.fixture(scope="session")
def mongo_test_url() -> str:
    return MONGO_URL
```

### tests/e2e/__init__.py
```
```

### tests/e2e/api/__init__.py
```
```

### tests/e2e/api/test_api.py
```
"""E2E API tests — FastAPI control plane."""
from __future__ import annotations

import pathlib

import pytest
from httpx import ASGITransport, AsyncClient


async def _make_app(tmp_path: pathlib.Path):  # type: ignore[return]
    from shell_ddd.bootstrap.container import ApplicationFactory
    from shell_ddd.framework.api.app import create_app

    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    container = await ApplicationFactory(database_url=db_url).build()
    return create_app(container)


class TestHealthEndpoint:
    async def test_health_returns_ok(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestTasksRouter:
    async def test_import_task(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "api_task.md"
        yaml_ = tmp_path / "api_task.yaml"
        md.write_text("# API Task", encoding="utf-8")
        yaml_.write_text("graph:\n  nodes: []\n", encoding="utf-8")

        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/tasks/import", json={
                "task_name": "api_task",
                "md_path": str(md),
                "yaml_path": str(yaml_),
            })
        assert resp.status_code == 201
        assert "task_id" in resp.json()

    async def test_get_task_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/tasks/no_such_task")
        assert resp.status_code == 404


class TestWorkflowsRouter:
    async def test_start_workflow_unknown_task_returns_error(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/workflows", json={"task_name": "no_such_task"})
        # Domain error → 404 or 400
        assert resp.status_code in (400, 404)

    async def test_start_and_get_workflow(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "wf_task.md"
        yaml_ = tmp_path / "wf_task.yaml"
        md.write_text("# WF Task", encoding="utf-8")
        yaml_.write_text("graph:\n  nodes: []\n", encoding="utf-8")

        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # import task first
            await client.post("/tasks/import", json={
                "task_name": "wf_task",
                "md_path": str(md),
                "yaml_path": str(yaml_),
            })
            # start workflow
            resp = await client.post("/workflows", json={"task_name": "wf_task"})
        assert resp.status_code == 201
        wf_id = resp.json()["workflow_id"]
        assert wf_id


class TestEnvelopesRouter:
    async def test_list_envelopes_empty(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/envelopes/workflow/nonexistent-wf")
        assert resp.status_code == 200
        assert resp.json()["envelopes"] == []


class TestNodesRouter:
    async def test_get_node_result_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/nodes/nonexistent-node/result?workflow_id=wf-x")
        assert resp.status_code == 404
```

### tests/e2e/cli/__init__.py
```
```

### tests/e2e/cli/test_cli.py
```
"""E2E CLI tests — exercises the CLI main entry-point using an in-process call
(asyncio.run + ApplicationFactory with temp SQLite DB) to avoid subprocess overhead
while still validating the full stack: CLI → bus → handler → SQL → result."""
from __future__ import annotations

import asyncio
import os
import pathlib

import pytest


def _db_url(tmp_path: pathlib.Path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"


class TestCliImportTask:
    async def test_import_task_happy_path(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "my_task.md"
        yaml_ = tmp_path / "my_task.yaml"
        md.write_text("# My Task", encoding="utf-8")
        yaml_.write_text("graph:\n  nodes: []\n", encoding="utf-8")

        os.environ["SHELL_DDD_DATABASE_URL"] = _db_url(tmp_path)
        try:
            from shell_ddd.framework.cli.main import _import_task
            rc = await _import_task([
                "--task-name", "my_task",
                "--task-dir", str(tmp_path),
            ])
        finally:
            del os.environ["SHELL_DDD_DATABASE_URL"]
        assert rc == 0

    async def test_import_task_missing_args_returns_1(self, tmp_path: pathlib.Path) -> None:
        os.environ["SHELL_DDD_DATABASE_URL"] = _db_url(tmp_path)
        try:
            from shell_ddd.framework.cli.main import _import_task
            rc = await _import_task([])
        finally:
            del os.environ["SHELL_DDD_DATABASE_URL"]
        assert rc == 1


class TestCliMain:
    def test_main_no_args_returns_1(self) -> None:
        from shell_ddd.framework.cli.main import main
        assert main([]) == 1

    def test_main_unknown_mode_returns_1(self) -> None:
        from shell_ddd.framework.cli.main import main
        assert main(["unknown_mode"]) == 1

    async def test_main_import_task_end_to_end(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "e2e_task.md"
        yaml_ = tmp_path / "e2e_task.yaml"
        md.write_text("# E2E Task", encoding="utf-8")
        yaml_.write_text("graph:\n  nodes: []\n", encoding="utf-8")

        os.environ["SHELL_DDD_DATABASE_URL"] = _db_url(tmp_path)
        try:
            from shell_ddd.framework.cli.main import _import_task
            rc = await _import_task(["--task-name", "e2e_task", "--task-dir", str(tmp_path)])
        finally:
            del os.environ["SHELL_DDD_DATABASE_URL"]
        assert rc == 0


class TestCliParser:
    def test_parser_defaults(self) -> None:
        from shell_ddd.framework.cli.parser import parse_args
        ns = parse_args([])
        assert ns.mode is None
        assert ns.node_dir is None
        assert ns.dry_run is False
        assert ns.add_dirs == []

    def test_parser_flags(self) -> None:
        from shell_ddd.framework.cli.parser import parse_args
        ns = parse_args([
            "--node-dir", "/tmp/node",
            "--mode", "agent",
            "--model", "gpt-4o",
            "--max-step", "10",
            "--dry-run",
        ])
        assert ns.node_dir == "/tmp/node"
        assert ns.mode == "agent"
        assert ns.model == "gpt-4o"
        assert ns.max_step == 10
        assert ns.dry_run is True
```

### tests/e2e/cli/test_tasker_full_graph.py
```
"""E2E test — Tasker full graph execution (Faza 10).

Uses InMemory adapters + FakeNodeProcessRunner so no real subprocess is spawned.
Verifies:
- RunTaskerWorkflowHandler creates a Workflow and runs all 3 graph nodes.
- NodeResult is persisted for every node (status = done/failed per runner config).
- Workflow final status = COMPLETED when all nodes succeed.
- Workflow final status = FAILED when any node fails.
- WorkflowCompleted / NodeCompleted events are published.
"""
from __future__ import annotations

import pytest

from shell_ddd.application.command_handlers.run_tasker_workflow_handler import RunTaskerWorkflowHandler
from shell_ddd.application.commands.commands import RunTaskerWorkflowCommand
from shell_ddd.application.queries.queries import GetWorkflowQuery
from shell_ddd.application.query_handlers.query_handlers import GetWorkflowHandler
from shell_ddd.domain.entities.task import Graph, GraphNode, Task
from shell_ddd.domain.events.events import NodeCompleted, NodeFailed, WorkflowCompleted, WorkflowFailed
from shell_ddd.domain.value_objects.ids import GraphId, NodeId, TaskId
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeNodeProcessRunner,
    InMemoryUnitOfWork,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task_with_graph(name: str, node_modes: list[str], uow_tasks_store: dict) -> Task:
    """Build a Task with a Graph containing len(node_modes) nodes and store it in place."""
    task_id = TaskId.generate()
    task_name = TaskName(name)
    graph_id = GraphId.generate()

    nodes = [
        GraphNode(
            id=NodeId(f"{name}-node-{i}"),
            position=i,
            node_dir=f"/fake/{mode}-{i}",
            mode=Mode(mode),
            role=mode,
            node_type=mode,
        )
        for i, mode in enumerate(node_modes)
    ]

    from datetime import UTC, datetime

    task = Task(
        id=task_id,
        name=task_name,
        version=1,
        hash=__import__("shell_ddd.domain.value_objects.hash", fromlist=["Hash"]).Hash.of("x"),
        body_md="# Task",
        body_yaml_raw="",
        is_current=True,
        created_at=datetime.now(tz=UTC),
        graph=Graph(
            id=graph_id,
            task_id=task_id,
            raw_dict={},
            nodes=nodes,
        ),
    )
    uow_tasks_store[task_id.value] = task
    return task


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def uow() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture()
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRunTaskerWorkflowHappyPath:
    """All 3 nodes succeed → workflow COMPLETED."""

    async def test_all_nodes_complete(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)
        _make_task_with_graph(
            "three-node-task",
            ["agent", "tool", "worker"],
            uow.tasks._store,
        )

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        workflow_id = await handler.handle(
            RunTaskerWorkflowCommand(task_name="three-node-task", work_dir="/tmp")
        )

        # Workflow persisted and marked complete
        dto = await GetWorkflowHandler(uow).handle(GetWorkflowQuery(workflow_id))
        assert dto is not None
        assert dto.status == "done"
        assert len(dto.node_states) == 3
        assert all(s.status == "done" for s in dto.node_states.values())

    async def test_three_node_results_saved(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(stdout="result", returncode=0)
        _make_task_with_graph("nr-task", ["agent", "tool", "worker"], uow.tasks._store)

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        await handler.handle(RunTaskerWorkflowCommand(task_name="nr-task", work_dir="/tmp"))

        results = list(uow.node_results._store.values())
        assert len(results) == 3
        assert all(r.status.value == "done" for r in results)
        assert all(r.stdout == "result" for r in results)

    async def test_events_published(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=0)
        _make_task_with_graph("ev-task", ["agent", "tool", "worker"], uow.tasks._store)

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        await handler.handle(RunTaskerWorkflowCommand(task_name="ev-task", work_dir="/tmp"))

        types = [type(e) for e in events.published]
        assert WorkflowCompleted in types
        assert types.count(NodeCompleted) == 3
        # No failures
        assert NodeFailed not in types
        assert WorkflowFailed not in types


class TestRunTaskerWorkflowPartialFailure:
    """One node returns non-zero → workflow FAILED."""

    async def test_workflow_marked_failed(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=1, stderr="crash")
        _make_task_with_graph(
            "fail-task",
            ["agent", "tool", "worker"],
            uow.tasks._store,
        )

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        workflow_id = await handler.handle(
            RunTaskerWorkflowCommand(task_name="fail-task", work_dir="/tmp")
        )

        dto = await GetWorkflowHandler(uow).handle(GetWorkflowQuery(workflow_id))
        assert dto is not None
        assert dto.status == "failed"

    async def test_workflow_failed_event_published(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=1)
        _make_task_with_graph("fail-ev-task", ["agent", "tool"], uow.tasks._store)

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        await handler.handle(RunTaskerWorkflowCommand(task_name="fail-ev-task", work_dir="/tmp"))

        types = [type(e) for e in events.published]
        assert WorkflowFailed in types
        assert WorkflowCompleted not in types


class TestRunTaskerWorkflowEdgeCases:
    async def test_empty_graph_creates_completed_workflow(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=0)
        _make_task_with_graph("empty-task", [], uow.tasks._store)

        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        workflow_id = await handler.handle(
            RunTaskerWorkflowCommand(task_name="empty-task", work_dir="/tmp")
        )

        dto = await GetWorkflowHandler(uow).handle(GetWorkflowQuery(workflow_id))
        assert dto is not None
        assert dto.status == "done"

    async def test_task_not_found_raises(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        from shell_ddd.domain.exceptions import TaskNotFound

        runner = FakeNodeProcessRunner(returncode=0)
        handler = RunTaskerWorkflowHandler(uow, clock, id_gen, runner, events)
        with pytest.raises(TaskNotFound):
            await handler.handle(
                RunTaskerWorkflowCommand(task_name="ghost-task", work_dir="/tmp")
            )
```

### tests/integration/__init__.py
```
```

### tests/integration/filesystem/__init__.py
```
```

### tests/integration/filesystem/test_filesystem.py
```
"""Integration tests for filesystem infrastructure (NodeWorkspace, TaskLoader, EnvelopeArchive)."""
from __future__ import annotations

import pytest

from shell_ddd.infrastructure.filesystem.node_workspace import NodeWorkspaceFs
from shell_ddd.infrastructure.filesystem.task_loader import FileSystemTaskLoader
from shell_ddd.infrastructure.filesystem.envelope_archive_fs import FileSystemEnvelopeArchive


# ---------------------------------------------------------------------------
# NodeWorkspaceFs
# ---------------------------------------------------------------------------


class TestNodeWorkspaceFs:
    async def test_prepare_creates_dot_node_subdirs(self, tmp_path: object) -> None:
        ws = NodeWorkspaceFs()
        path = await ws.prepare("my-node", str(tmp_path))

        import pathlib
        dot_node = pathlib.Path(path) / ".node"
        assert dot_node.exists()
        for subdir in ["input", "output", "logs", "temp", "prompt"]:
            assert (dot_node / subdir).is_dir(), f".node/{subdir} should be a directory"

    async def test_prepare_returns_workspace_path(self, tmp_path: object) -> None:
        ws = NodeWorkspaceFs()
        path = await ws.prepare("node-abc", str(tmp_path))
        import pathlib
        assert pathlib.Path(path).name == "node-abc"

    async def test_cleanup_removes_workspace(self, tmp_path: object) -> None:
        ws = NodeWorkspaceFs()
        path = await ws.prepare("node-to-clean", str(tmp_path))
        import pathlib
        assert pathlib.Path(path).exists()
        await ws.cleanup(path)
        assert not pathlib.Path(path).exists()

    async def test_write_and_read_output(self, tmp_path: object) -> None:
        ws = NodeWorkspaceFs()
        path = await ws.prepare("node-io", str(tmp_path))
        out = await ws.write_output(path, "result.txt", "hello world")
        import pathlib
        assert pathlib.Path(out).read_text() == "hello world"

    async def test_read_input_missing_returns_empty(self, tmp_path: object) -> None:
        ws = NodeWorkspaceFs()
        path = await ws.prepare("node-empty-input", str(tmp_path))
        content = await ws.read_input(path)
        assert content == ""


# ---------------------------------------------------------------------------
# FileSystemTaskLoader
# ---------------------------------------------------------------------------


class TestFileSystemTaskLoader:
    async def test_load_reads_both_files(self, tmp_path: object) -> None:
        import pathlib
        md = pathlib.Path(str(tmp_path)) / "task.md"
        yaml = pathlib.Path(str(tmp_path)) / "task.yaml"
        md.write_text("# My Task", encoding="utf-8")
        yaml.write_text("graph: []", encoding="utf-8")

        loader = FileSystemTaskLoader()
        body_md, body_yaml = await loader.load(str(md), str(yaml))
        assert body_md == "# My Task"
        assert body_yaml == "graph: []"


# ---------------------------------------------------------------------------
# FileSystemEnvelopeArchive
# ---------------------------------------------------------------------------


class TestFileSystemEnvelopeArchive:
    async def test_archive_writes_json_file(self, tmp_path: object) -> None:
        from datetime import UTC, datetime

        from shell_ddd.domain.entities.envelope import Envelope
        from shell_ddd.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
        from shell_ddd.domain.value_objects.ids import EnvelopeId, NodeId, WorkflowId

        archive = FileSystemEnvelopeArchive(str(tmp_path))
        now = datetime.now(tz=UTC)
        envelope = Envelope.new(
            id_=EnvelopeId("env-arch-1"),
            workflow_id=WorkflowId("wf-arch-1"),
            sender_node_id=NodeId("node-s"),
            receiver_node_id=NodeId("node-r"),
            source_role="agent",
            target_role="worker",
            now=now,
        )
        uri = await archive.archive(envelope)
        assert uri.startswith("fs://archive/wf-arch-1/env-arch-1")

        import json, pathlib
        stored = json.loads((pathlib.Path(str(tmp_path)) / "wf-arch-1" / "env-arch-1.json").read_text())
        assert stored["id"] == "env-arch-1"
        assert stored["workflow_id"] == "wf-arch-1"
```

### tests/integration/mongo/__init__.py
```
```

### tests/integration/process/__init__.py
```
```

### tests/integration/process/test_subprocess_runner.py
```
"""Integration tests for SubprocessNodeProcessRunner."""
from __future__ import annotations

import sys

import pytest

from shell_ddd.infrastructure.process.subprocess_runner import SubprocessNodeProcessRunner
from shell_ddd.domain.value_objects.manifest import Manifest
from shell_ddd.domain.value_objects.mode import Mode


def _make_manifest(name: str, mode: Mode = Mode.WORKER) -> Manifest:
    return Manifest(name=name, mode=mode, role=str(mode), node_type="node", version="0")


class TestSubprocessNodeProcessRunner:
    async def test_echo_stdout(self, tmp_path: object) -> None:
        runner = SubprocessNodeProcessRunner()
        # Use python -c "print('ok')" so tests work on Windows and Linux
        manifest = _make_manifest(name=sys.executable, mode=Mode.WORKER)
        result = await runner._run_argv(
            [sys.executable, "-c", "print('ok')"],
            cwd=str(tmp_path),
            env={},
        )
        assert result.returncode == 0
        assert "ok" in result.stdout

    async def test_stderr_captured(self, tmp_path: object) -> None:
        runner = SubprocessNodeProcessRunner()
        result = await runner._run_argv(
            [sys.executable, "-c", "import sys; sys.stderr.write('err')"],
            cwd=str(tmp_path),
            env={},
        )
        assert result.returncode == 0
        assert "err" in result.stderr

    async def test_nonzero_returncode(self, tmp_path: object) -> None:
        runner = SubprocessNodeProcessRunner()
        result = await runner._run_argv(
            [sys.executable, "-c", "raise SystemExit(42)"],
            cwd=str(tmp_path),
            env={},
        )
        assert result.returncode == 42

    async def test_timeout_returns_negative_one(self, tmp_path: object) -> None:
        runner = SubprocessNodeProcessRunner()
        result = await runner._run_argv(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cwd=str(tmp_path),
            env={},
            timeout=0.2,
        )
        assert result.returncode == -1
        assert "timed out" in result.stderr.lower()
```

### tests/integration/sql_postgres/__init__.py
```
```

### tests/integration/sql_postgres/test_sql_postgres.py
```
"""PostgreSQL integration tests — mirrors sql_sqlite tests on a real Postgres instance.

Skip all tests when PG_TEST_URL is not set:
    export PG_TEST_URL=postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test

Start Postgres via docker-compose:
    docker compose -f shell_ddd/docker-compose.test.yml up -d postgres
"""
from __future__ import annotations

import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from shell_ddd.application.command_handlers.import_task_handler import ImportTaskHandler
from shell_ddd.application.command_handlers.save_node_result_handler import SaveNodeResultHandler
from shell_ddd.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell_ddd.application.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell_ddd.application.commands.commands import (
    ImportTaskCommand,
    SaveNodeResultCommand,
    SavePromptCommand,
    StartWorkflowCommand,
)
from shell_ddd.application.queries.queries import (
    GetCurrentTaskQuery,
    GetNodeResultQuery,
    GetPromptQuery,
    GetWorkflowQuery,
)
from shell_ddd.application.query_handlers.query_handlers import (
    GetCurrentTaskHandler,
    GetNodeResultHandler,
    GetPromptHandler,
    GetWorkflowHandler,
)
from shell_ddd.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell_ddd.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeTaskLoader,
)
from shell_ddd.infrastructure.persistence.sql import build_session_factory, create_all_tables

_PG_URL = os.environ.get(
    "PG_TEST_URL", "postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test"
)

pytestmark = pytest.mark.skipif(
    os.environ.get("PG_TEST_URL") is None,
    reason="PG_TEST_URL not set — start Postgres via docker-compose and set PG_TEST_URL",
)


# ---------------------------------------------------------------------------
# Fixtures (module-scoped DB with fresh schema, function-scoped UoW)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def session_factory() -> async_sessionmaker:  # type: ignore[type-arg]
    await create_all_tables(_PG_URL)
    return build_session_factory(_PG_URL)


@pytest.fixture()
def uow(session_factory: async_sessionmaker) -> SqlAlchemyUnitOfWork:  # type: ignore[type-arg]
    return SqlAlchemyUnitOfWork(session_factory)


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture()
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def task_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# PG Task", yaml_raw="graph: []")


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class TestPgTaskRepository:
    async def test_import_and_get_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await handler.handle(ImportTaskCommand("t.md", "t.yaml", "pg-task"))

        q = GetCurrentTaskHandler(uow)
        dto = await q.handle(GetCurrentTaskQuery("pg-task"))
        assert dto is not None
        assert dto.name == "pg-task"
        assert dto.is_current is True

    async def test_reimport_marks_old_non_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await handler.handle(ImportTaskCommand("t.md", "t.yaml", "pg-task-v"))
        await handler.handle(ImportTaskCommand("t.md", "t.yaml", "pg-task-v"))

        q = GetCurrentTaskHandler(uow)
        dto = await q.handle(GetCurrentTaskQuery("pg-task-v"))
        assert dto is not None
        assert dto.is_current is True


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


class TestPgWorkflowRepository:
    async def test_start_and_query_workflow(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
    ) -> None:
        imp = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await imp.handle(ImportTaskCommand("t.md", "t.yaml", "pg-wf-task"))

        start = StartWorkflowHandler(uow, clock, id_gen, events)
        wf_id = await start.handle(StartWorkflowCommand("pg-wf-task"))

        q = GetWorkflowHandler(uow)
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"
        assert dto.task_name == "pg-wf-task"

    async def test_workflow_not_found_returns_none(
        self,
        uow: SqlAlchemyUnitOfWork,
    ) -> None:
        q = GetWorkflowHandler(uow)
        dto = await q.handle(GetWorkflowQuery("pg-no-such-wf"))
        assert dto is None


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------


class TestPgPromptRepository:
    async def test_save_and_get_prompt(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("pg-sys-prompt", "You are a pg helper."))

        q = GetPromptHandler(uow)
        dto = await q.handle(GetPromptQuery("pg-sys-prompt"))
        assert dto is not None
        assert dto.body == "You are a pg helper."

    async def test_prompt_not_found_returns_none(
        self,
        uow: SqlAlchemyUnitOfWork,
    ) -> None:
        q = GetPromptHandler(uow)
        dto = await q.handle(GetPromptQuery("pg-missing-prompt"))
        assert dto is None


# ---------------------------------------------------------------------------
# NodeResult
# ---------------------------------------------------------------------------


class TestPgNodeResultRepository:
    async def test_save_and_get_result(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        handler = SaveNodeResultHandler(uow, clock, id_gen, events)
        await handler.handle(
            SaveNodeResultCommand(
                workflow_id="pg-wf-nr-1",
                node_id="pg-node-nr-1",
                status="done",
                stdout="pg success",
            )
        )

        q = GetNodeResultHandler(uow)
        dto = await q.handle(GetNodeResultQuery("pg-node-nr-1", "pg-wf-nr-1"))
        assert dto is not None
        assert dto.stdout == "pg success"
        assert dto.status == "done"


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------


class TestPgUnitOfWorkRollback:
    async def test_rollback_on_exception_leaves_db_clean(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        try:
            async with uow as u:
                from shell_ddd.domain.entities.prompt import Prompt
                from shell_ddd.domain.value_objects.ids import PromptId

                await u.prompts.save(
                    Prompt.new(
                        id_=PromptId("pg-rollback-prompt-x"),
                        name="pg-rollback-prompt-x",
                        body="should not persist",
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced pg rollback")
        except RuntimeError:
            pass

        q = GetPromptHandler(uow)
        dto = await q.handle(GetPromptQuery("pg-rollback-prompt-x"))
        assert dto is None
```

### tests/integration/sql_sqlite/__init__.py
```
"""SQLite integration test package."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.entities.prompt import Prompt
from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.value_objects.ids import (
    NodeId,
    NodeResultId,
    PromptId,
    TaskId,
    WorkflowId,
)
from shell_ddd.domain.value_objects.status import Status
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell_ddd.infrastructure.persistence.memory.memory import FakeClock
from shell_ddd.infrastructure.persistence.sql import build_session_factory, create_all_tables


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def session_factory(tmp_path_factory: pytest.TempPathFactory) -> async_sessionmaker:  # type: ignore[type-arg]
    db = tmp_path_factory.mktemp("sqlite") / "test.db"
    url = f"sqlite+aiosqlite:///{db}"
    await create_all_tables(url)
    return build_session_factory(url)


@pytest.fixture()
def uow(session_factory: async_sessionmaker) -> SqlAlchemyUnitOfWork:  # type: ignore[type-arg]
    return SqlAlchemyUnitOfWork(session_factory)


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


# ---------------------------------------------------------------------------
# Task repository
# ---------------------------------------------------------------------------


class TestSqlTaskRepository:
    async def test_save_and_get_by_id(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        task = Task.new(
            id_=TaskId("task-sql-1"),
            name=TaskName("sql-task"),
            body_md="# hello",
            body_yaml_raw="graph: []",
            now=clock.now(),
        )
        async with uow as u:
            await u.tasks.save(task)
            await u.commit()

        async with uow as u:
            result = await u.tasks.get_by_id(TaskId("task-sql-1"))
        assert result is not None
        assert result.name == TaskName("sql-task")
        assert result.is_current is True

    async def test_get_nonexistent_returns_none(
        self, uow: SqlAlchemyUnitOfWork
    ) -> None:
        async with uow as u:
            result = await u.tasks.get_by_id(TaskId("nonexistent"))
        assert result is None

    async def test_get_current_by_name(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        task = Task.new(
            id_=TaskId("task-sql-2"),
            name=TaskName("current-task"),
            body_md="# current",
            body_yaml_raw="graph: []",
            now=clock.now(),
        )
        async with uow as u:
            await u.tasks.save(task)
            await u.commit()

        async with uow as u:
            result = await u.tasks.get_current_by_name(TaskName("current-task"))
        assert result is not None
        assert result.id == TaskId("task-sql-2")


# ---------------------------------------------------------------------------
# Workflow repository
# ---------------------------------------------------------------------------


class TestSqlWorkflowRepository:
    async def test_save_and_get_workflow(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        wf = Workflow.new(
            id_=WorkflowId("wf-sql-1"),
            task_name="wf-task",
            now=clock.now(),
        )
        async with uow as u:
            await u.workflows.save(wf)
            await u.commit()

        async with uow as u:
            result = await u.workflows.get_by_id(WorkflowId("wf-sql-1"))
        assert result is not None
        assert result.task_name == "wf-task"

    async def test_workflow_not_found_returns_none(
        self, uow: SqlAlchemyUnitOfWork
    ) -> None:
        async with uow as u:
            result = await u.workflows.get_by_id(WorkflowId("no-such-wf"))
        assert result is None


# ---------------------------------------------------------------------------
# Prompt repository
# ---------------------------------------------------------------------------


class TestSqlPromptRepository:
    async def test_save_and_get_prompt(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        prompt = Prompt.new(
            id_=PromptId("prompt-sql-1"),
            name="sys-prompt",
            body="You are helpful.",
            now=clock.now(),
        )
        async with uow as u:
            await u.prompts.save(prompt)
            await u.commit()

        async with uow as u:
            result = await u.prompts.get_current_by_name("sys-prompt")
        assert result is not None
        assert result.body == "You are helpful."

    async def test_prompt_not_found_returns_none(
        self, uow: SqlAlchemyUnitOfWork
    ) -> None:
        async with uow as u:
            result = await u.prompts.get_current_by_name("missing-prompt")
        assert result is None


# ---------------------------------------------------------------------------
# NodeResult repository
# ---------------------------------------------------------------------------


class TestSqlNodeResultRepository:
    async def test_save_and_get_node_result(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        result_entity = NodeResult.new(
            id_=NodeResultId("nr-sql-1"),
            node_id=NodeId("node-1"),
            workflow_id=WorkflowId("wf-nr-1"),
            status=Status.done(),
            stdout="output",
            stderr="",
            now=clock.now(),
        )
        async with uow as u:
            await u.node_results.save(result_entity)
            await u.commit()

        async with uow as u:
            found = await u.node_results.get_by_node_and_workflow(
                NodeId("node-1"), WorkflowId("wf-nr-1")
            )
        assert found is not None
        assert found.status == Status.done()
        assert found.stdout == "output"


# ---------------------------------------------------------------------------
# UnitOfWork rollback
# ---------------------------------------------------------------------------


class TestSqlUnitOfWorkRollback:
    async def test_rollback_on_exception_leaves_db_clean(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        prompt = Prompt.new(
            id_=PromptId("rollback-prompt"),
            name="rollback-prompt",
            body="should not persist",
            now=clock.now(),
        )
        try:
            async with uow as u:
                await u.prompts.save(prompt)
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        async with uow as u:
            result = await u.prompts.get_current_by_name("rollback-prompt")
        assert result is None


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture()
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def task_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# SQL Task", yaml_raw="graph: []")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSqlTaskRepository:
    async def test_save_and_get_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await handler.handle(ImportTaskCommand("t.md", "t.yaml", "sql-task"))

        q = GetCurrentTaskHandler(uow)
        dto = await q.handle(GetCurrentTaskQuery("sql-task"))
        assert dto is not None
        assert dto.name == "sql-task"
        assert dto.is_current is True

    async def test_reimport_makes_old_non_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await handler.handle(ImportTaskCommand("t.md", "t.yaml", "sql-task-v"))
        await handler.handle(ImportTaskCommand("t.md", "t.yaml", "sql-task-v"))

        q = GetCurrentTaskHandler(uow)
        dto = await q.handle(GetCurrentTaskQuery("sql-task-v"))
        assert dto is not None
        assert dto.is_current is True


class TestSqlWorkflowRepository:
    async def test_start_and_query_workflow(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
    ) -> None:
        imp = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await imp.handle(ImportTaskCommand("t.md", "t.yaml", "wf-task"))

        start = StartWorkflowHandler(uow, clock, id_gen, events)
        wf_id = await start.handle(StartWorkflowCommand("wf-task"))

        q = GetWorkflowHandler(uow)
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"
        assert dto.task_name == "wf-task"


class TestSqlPromptRepository:
    async def test_save_and_get_prompt(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("sys-prompt", "You are helpful."))

        q = GetPromptHandler(uow)
        dto = await q.handle(GetPromptQuery("sys-prompt"))
        assert dto is not None
        assert dto.body == "You are helpful."


class TestSqlNodeResultRepository:
    async def test_save_and_get_result(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        handler = SaveNodeResultHandler(uow, clock, id_gen, events)
        await handler.handle(
            SaveNodeResultCommand(
                workflow_id="wf-sql-1",
                node_id="node-sql-1",
                status="done",
                stdout="success",
            )
        )

        q = GetNodeResultHandler(uow)
        dto = await q.handle(GetNodeResultQuery("node-sql-1", "wf-sql-1"))
        assert dto is not None
        assert dto.stdout == "success"
        assert dto.status == "done"


class TestSqlCommitRollback:
    async def test_rollback_on_exception(
        self,
        session_factory: async_sessionmaker,  # type: ignore[type-arg]
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        uow = SqlAlchemyUnitOfWork(session_factory)
        try:
            async with uow as u:
                await u.prompts.save(
                    __import__(
                        "shell_ddd.domain.entities.prompt", fromlist=["Prompt"]
                    ).Prompt.new(
                        id_=id_gen.new_prompt_id(),
                        name="rollback-prompt",
                        body="body",
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        uow2 = SqlAlchemyUnitOfWork(session_factory)
        q = GetPromptHandler(uow2)
        dto = await q.handle(GetPromptQuery("rollback-prompt"))
        assert dto is None
```
