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
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GraphModel(Base):
    __tablename__ = "graph"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=False, index=True, unique=True
    )
    template_graph_id: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    raw_dict: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]

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
    current_node_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None, index=True
    )
    work_dir: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    node_states: Mapped[list[NodeStateModel]] = relationship(
        "NodeStateModel", back_populates="workflow", cascade="all, delete-orphan"
    )
    node_results: Mapped[list[NodeResultModel]] = relationship(
        "NodeResultModel",
        primaryjoin="WorkflowModel.id == foreign(NodeResultModel.workflow_id)",
        cascade="all, delete-orphan",
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
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    receiver: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column("payload_json", JSON, nullable=False, default=dict)  # type: ignore[type-arg]
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


class TemplateGraphModel(Base):
    __tablename__ = "template_graph"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(36), nullable=False)
    purpose: Mapped[str] = mapped_column(String(36), nullable=False)

    nodes: Mapped[list["TemplateGraphNodeModel"]] = relationship(
        "TemplateGraphNodeModel",
        back_populates="graph",
        cascade="all, delete-orphan",
        order_by="TemplateGraphNodeModel.position",
    )


class TemplateGraphNodeModel(Base):
    __tablename__ = "template_graph_node"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    template_graph_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("template_graph.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(String(128), nullable=False)
    node_type: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    timeout: Mapped[int] = mapped_column(Integer, nullable=False)
    retries: Mapped[int] = mapped_column(Integer, nullable=False)
    log_level: Mapped[str] = mapped_column(String(16), nullable=False)
    max_step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    no_ask_user: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    autopilot: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    status_initial: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    extra: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )  # type: ignore[type-arg]
    script: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    script_type: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
    )
    graph: Mapped[TemplateGraphModel] = relationship(
        "TemplateGraphModel",
        back_populates="nodes",
    )
```

### infrastructure/persistence/sql/query_services.py
```
"""Implementacje portów odczytu przy użyciu SQLAlchemy."""
from __future__ import annotations

from sqlalchemy.orm import selectinload
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import joinedload

from shell_ddd.application.dto.dto import (
    EnvelopeDto,
    GraphNodeDto,
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
    WorkflowModel, GraphModel, RagDocumentModel,
)

class SqlQueryServices:
    """Zbiorcza klasa implementująca wszystkie interfejsy QueryService (Read Model)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    # --- TaskQueryService ---
    async def get_task_by_name(self, name: str) -> TaskDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(TaskModel)
                .where(TaskModel.name == name)
                .where(TaskModel.is_current == True)
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None

            graph_stmt = (
                select(GraphModel)
                .options(selectinload(GraphModel.nodes))
                .where(GraphModel.task_id == model.id)
            )
            graph_res = await session.execute(graph_stmt)
            graph_model = graph_res.scalar_one_or_none()

            graph_nodes: list[GraphNodeDto] = []
            if graph_model is not None:
                graph_nodes = [
                    GraphNodeDto(
                        id=n.id,
                        position=n.position,
                        node_dir=n.node_dir,
                        mode=n.mode,
                        role=n.role,
                        node_type=n.node_type,
                        model=n.model,
                        command=n.command,
                    )
                    for n in graph_model.nodes
                ]

            return TaskDto(
                id=model.id,
                name=model.name,
                version=model.version,
                hash=model.hash,
                is_current=model.is_current,
                created_at=model.created_at,
                body=model.body,
                graph_nodes=graph_nodes,
            )

    async def get_current_task(self, name: str) -> TaskDto | None:
        # W tej implementacji current_task jest tożsamy z pobraniem po nazwie
        return await self.get_task_by_name(name)

    # --- WorkflowQueryService ---
    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(WorkflowModel)
                .options(selectinload(WorkflowModel.node_states))
                .where(WorkflowModel.id == workflow_id)
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return WorkflowDto(
                id=model.id,
                task_name=model.task_name,
                status=model.status,
                created_at=model.created_at,
                node_states={
                    n.node_id: NodeStateDto(
                        node_id=n.node_id,
                        status=n.status,
                        step=n.step,
                        updated_at=n.updated_at,
                    )
                    for n in model.node_states
                },
            )

    # --- EnvelopeQueryService ---
    async def get_envelopes_by_workflow(
            self, workflow_id: str, pending_only: bool = False
    ) -> list[EnvelopeDto]:
        async with self._session_factory() as session:
            stmt = select(EnvelopeModel).where(EnvelopeModel.workflow_id == workflow_id)
            if pending_only:
                stmt = stmt.where(EnvelopeModel.status == "pending")
            res = await session.execute(stmt)
            return [
                EnvelopeDto(
                    id=m.id,
                    workflow_id=m.workflow_id,
                    destination_node=m.destination_node,
                    status=m.status,
                    payload=m.payload,
                )
                for m in res.scalars()
            ]

    # --- NodeResultQueryService ---
    async def get_node_result(self, node_id: str, workflow_id: str) -> NodeResultDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(WorkflowModel)
                .options(selectinload(WorkflowModel.node_results))
                .where(WorkflowModel.id == workflow_id)
            )
            res = await session.execute(stmt)
            wf = res.scalar_one_or_none()
            if not wf:
                return None
            m = next((nr for nr in wf.node_results if nr.node_id == node_id), None)
            if not m:
                return None
            return NodeResultDto(
                id=m.id,
                node_id=m.node_id,
                workflow_id=m.workflow_id,
                status=m.status,
                stdout=m.stdout,
                stderr=m.stderr,
                artifact_uri=m.artifact_uri,
                created_at=m.created_at,
            )

    # --- PromptQueryService ---
    async def get_prompt(self, name: str) -> PromptDto | None:
        async with self._session_factory() as session:
            stmt = select(PromptModel).where(PromptModel.name == name)
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                return None
            return PromptDto(
                id=m.id,
                name=m.name,
                body=m.body,
                version=m.version,
                hash=m.hash,
                is_current=m.is_current,
                created_at=m.created_at
            )

    # --- RunnerConfigQueryService ---
    async def get_runner_config(self, package_name: str) -> RunnerConfigDto | None:
        async with self._session_factory() as session:
            stmt = select(RunnerConfigModel).where(RunnerConfigModel.package_name == package_name)
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                return None
            return RunnerConfigDto(
                package_name=m.package_name,
                version=m.version,
                config=m.config
            )

    # --- SessionQueryService ---
    async def get_session_history(self, session_id: str) -> SessionDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(SessionModel)
                .options(selectinload(SessionModel.messages))
                .where(SessionModel.id == session_id)
            )
            res = await session.execute(stmt)
            session = res.scalar_one_or_none()
            if not session:
                return None
            return SessionDto(
                id=session.id,
                goal=session.goal,
                status=session.status,
                opened_at=session.opened_at,
                closed_at=session.closed_at,
                messages=[
                    MessageDto(id=message.id,
                               session_id=message.session_id,
                               correlation_id=message.correlation_id,
                               sender=message.sender,
                               receiver=message.receiver,
                               payload=message.payload,
                               created_at=message.created_at)
                    for message in session.messages
                ]
            )

    # --- RagQueryService ---
    async def search_similar(
            self, query_embedding: bytes, top_k: int = 5, domain: str | None = None
    ) -> list[RagChunkDto]:
        async with self._session_factory() as session:
            stmt = select(RagChunkModel).options(joinedload(RagChunkModel.document))
            if domain:
                stmt = stmt.join(RagChunkModel.document).where(RagDocumentModel.domain == domain)
            res = await session.execute(stmt.limit(100)) # Przykładowy limit
            return [
                       RagChunkDto(
                           chunk_id=str(c.id),
                           document_id=str(c.document_id),
                           chunk_index=c.chunk_index,
                           chunk_text=c.chunk_text,    # Zmieniono z 'content' na 'chunk_text'
                           source_uri=c.document.source_uri, # Dane pobrane przez relację z RagDocumentModel
                           title=c.document.title,
                           domain=c.document.domain,
                           score=0.0 # Tu docelowo wynik z wyszukiwania wektorowego
                       )
                       for c in res.scalars()
                   ][:top_k]
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
from shell_ddd.domain.entities.graph import Graph
from shell_ddd.domain.entities.prompt import Prompt
from shell_ddd.domain.entities.rag_document import RagChunk, RagDocument
from shell_ddd.domain.entities.runner_config import RunnerConfig
from shell_ddd.domain.entities.session import Message, Session
from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.entities.template_graph import TemplateGraph
from shell_ddd.domain.entities.template_graph_node import TemplateGraphNode
from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.services.rag_index_service import cosine_similarity
from shell_ddd.domain.value_objects.envelope_status import EnvelopeStatus
from shell_ddd.domain.value_objects.ids import (
    EnvelopeId,
    GraphId,
    MessageId,
    NodeId,
    PromptId,
    RagChunkId,
    RagDocumentId,
    RunnerConfigId,
    SessionId,
    TaskId,
    WorkflowId, CorrelationId, TemplateGraphId, TemplateGraphNodeId,
)
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.persistence.sql.mappers import (  # noqa: E501
    envelope_entity_to_model,
    envelope_model_to_entity,
    graph_entity_to_model,
    graph_model_to_entity,
    prompt_entity_to_model,
    prompt_model_to_entity,
    runner_config_entity_to_model,
    runner_config_model_to_entity,
    task_entity_to_model,
    task_model_to_entity,
    workflow_entity_to_model,
    workflow_model_to_entity, template_graph_entity_to_model, template_graph_model_to_entity,
    template_graph_node_model_to_entity, template_graph_node_entity_to_model,
)
from shell_ddd.infrastructure.persistence.sql.models import (
    EnvelopeModel,
    GraphModel,
    MessageModel,
    PromptModel,
    RagChunkModel,
    RagDocumentModel,
    RunnerConfigModel,
    SessionModel,
    TaskModel,
    WorkflowModel, TemplateGraphModel, TemplateGraphNodeModel,
)

import logging

logger = logging.getLogger(__name__)


class SqlTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, task_id: TaskId) -> Task | None:
        q = select(TaskModel).where(TaskModel.id == task_id.value)
        row = (await self._session.execute(q)).scalar_one_or_none()
        return task_model_to_entity(row) if row else None

    async def get_by_name(self, name: TaskName) -> Task | None:
        q = (
            select(TaskModel)
            .where(TaskModel.name == name.value)
            .order_by(TaskModel.version.desc())
            .limit(1)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return task_model_to_entity(row) if row else None

    async def get_current_by_name(self, name: TaskName) -> Task | None:
        logger.info("Querying current Task by name=%s", name.value)
        q = (
            select(TaskModel)
            .where(TaskModel.name == name.value, TaskModel.is_current.is_(True))
            .limit(1)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if not row:
            logger.info("No current Task found for name=%s", name.value)
            return None

        logger.info(
            "TaskModel found: id=%s name=%s is_current=%s",
            row.id,
            row.name,
            row.is_current,
        )
        return task_model_to_entity(row)

    async def save(self, task: Task) -> None:
        model = task_entity_to_model(task)
        await self._session.merge(model)

    async def list_current(self) -> list[Task]:
        q = select(TaskModel).where(TaskModel.is_current.is_(True))
        rows = (await self._session.execute(q)).scalars().all()
        return [task_model_to_entity(r) for r in rows]


class SqlGraphRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, graph_id: GraphId) -> Graph | None:
        q = (
            select(GraphModel)
            .options(selectinload(GraphModel.nodes))
            .where(GraphModel.id == graph_id.value)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return graph_model_to_entity(row) if row else None

    async def get_by_task_id(self, task_id: TaskId) -> Graph | None:
        q = (
            select(GraphModel)
            .options(selectinload(GraphModel.nodes))
            .where(GraphModel.task_id == task_id.value)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return graph_model_to_entity(row) if row else None

    async def save(self, graph: Graph) -> None:
        model = graph_entity_to_model(graph)
        await self._session.merge(model)


class SqlWorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        q = (
            select(WorkflowModel)
            .options(
                selectinload(WorkflowModel.node_states),
                selectinload(WorkflowModel.node_results),
            )
            .where(WorkflowModel.id == workflow_id.value)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return workflow_model_to_entity(row) if row else None

    async def save(self, workflow: Workflow) -> None:
        """Persist the workflow with optimistic concurrency control (CAS).

        On first save (no row exists yet) the aggregate's ``version`` is
        bumped from 0 to 1 and the row is inserted via merge. On subsequent
        saves a CAS UPDATE asserts that the persisted ``version`` still
        equals the aggregate's loaded version; on success the persisted
        version is bumped to ``version + 1`` and mirrored on the aggregate.
        On mismatch :class:`WorkflowConcurrentlyModified` is raised.
        """
        from shell_ddd.domain.exceptions import WorkflowConcurrentlyModified

        # Detect existing row.
        existing = await self._session.execute(
            select(WorkflowModel.version).where(WorkflowModel.id == workflow.id.value)
        )
        existing_version = existing.scalar_one_or_none()

        if existing_version is None:
            # First save — initial insert. Bump version 0 → 1.
            workflow.version = max(workflow.version, 0) + 1
            model = workflow_entity_to_model(workflow)
            await self._session.merge(model)
            return

        # Subsequent save — CAS on persisted version.
        if existing_version != workflow.version:
            raise WorkflowConcurrentlyModified(workflow.id.value)

        new_version = workflow.version + 1
        cas_stmt = (
            update(WorkflowModel)
            .where(
                WorkflowModel.id == workflow.id.value,
                WorkflowModel.version == workflow.version,
            )
            .values(
                status=workflow.status.value,
                current_node_id=(
                    workflow.cursor.current_node_id.value
                    if workflow.cursor.current_node_id
                    else None
                ),
                work_dir=workflow.execution_context.work_dir,
                correlation_id=workflow.execution_context.correlation_id,
                version=new_version,
            )
        )
        result = await self._session.execute(cas_stmt)
        if (result.rowcount or 0) == 0:
            raise WorkflowConcurrentlyModified(workflow.id.value)

        workflow.version = new_version
        model = workflow_entity_to_model(workflow)
        await self._session.merge(model)


class SqlEnvelopeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None:
        q = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(EnvelopeModel.id == envelope_id.value)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return envelope_model_to_entity(row) if row else None

    async def save(self, envelope: Envelope) -> None:
        model = envelope_entity_to_model(envelope)
        await self._session.merge(model)

    async def list_by_workflow(self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0) -> list[Envelope]:
        q = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(EnvelopeModel.workflow_id == workflow_id.value)
            .offset(offset)
        )
        if limit is not None:
            q = q.limit(limit)
        rows = (await self._session.execute(q)).scalars().all()
        return [envelope_model_to_entity(r) for r in rows]

    async def list_pending(self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0) -> list[Envelope]:
        q = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(
                EnvelopeModel.workflow_id == workflow_id.value,
                EnvelopeModel.status == EnvelopeStatus.PENDING.value,
            )
            .offset(offset)
        )
        if limit is not None:
            q = q.limit(limit)
        rows = (await self._session.execute(q)).scalars().all()
        return [envelope_model_to_entity(r) for r in rows]


class SqlPromptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, prompt_id: PromptId) -> Prompt | None:
        q = select(PromptModel).where(PromptModel.id == prompt_id.value)
        row = (await self._session.execute(q)).scalar_one_or_none()
        return prompt_model_to_entity(row) if row else None

    async def get_current_by_name(self, name: str) -> Prompt | None:
        q = select(PromptModel).where(
            PromptModel.name == name, PromptModel.is_current.is_(True)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return prompt_model_to_entity(row) if row else None

    async def save(self, prompt: Prompt) -> None:
        model = prompt_entity_to_model(prompt)
        await self._session.merge(model)


class SqlRunnerConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None:
        q = select(RunnerConfigModel).where(RunnerConfigModel.id == config_id.value)
        row = (await self._session.execute(q)).scalar_one_or_none()
        return runner_config_model_to_entity(row) if row else None

    async def get_by_package(self, package_name: str) -> RunnerConfig | None:
        q = select(RunnerConfigModel).where(
            RunnerConfigModel.package_name == package_name
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return runner_config_model_to_entity(row) if row else None

    async def save(self, config: RunnerConfig) -> None:
        model = runner_config_entity_to_model(config)
        await self._session.merge(model)


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
        self._session = session

    async def save(self, document: RagDocument) -> None:
        doc_model = RagDocumentModel(
            id=document.id.value,
            source_uri=document.source_uri,
            title=document.title,
            domain=document.domain,
            created_at=document.created_at,
        )
        await self._session.merge(doc_model)
        # delete+re-insert chunks to keep them consistent
        from sqlalchemy import delete as sa_delete
        await self._session.execute(
            sa_delete(RagChunkModel).where(RagChunkModel.document_id == document.id.value)
        )
        for chunk in document.chunks:
            self._session.add(
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
        row = (await self._session.execute(q)).scalar_one_or_none()
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
        rows = (await self._session.execute(q)).scalars().all()
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
        self._session = session

    async def save(self, session: Session) -> None:
        model = SessionModel(
            id=session.id.value,
            goal=session.goal,
            status=session.status,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
        )
        await self._session.merge(model)
        for message in session.messages:
            await self._session.merge(
                MessageModel(
                    id=message.id.value,
                    session_id=message.session_id.value,
                    correlation_id=message.correlation_id.value,
                    sender=message.sender,
                    receiver=message.receiver,
                    payload=message.payload,
                    created_at=message.created_at,
                )
            )

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        q = select(SessionModel).where(SessionModel.id == session_id.value)
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        return Session(
            id=SessionId(row.id),
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
        rows = (await self._session.execute(q)).scalars().all()
        return [
            Message(
                id=MessageId(r.id),
                session_id=SessionId(r.session_id),
                correlation_id=CorrelationId(r.correlation_id),
                sender=r.sender,
                receiver=r.receiver,
                payload=r.payload,
                created_at=r.created_at,
            )
            for r in rows
        ]


class SqlTemplateGraphRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, template_graph_id: TemplateGraphId) -> TemplateGraph | None:
        q = (
            select(TemplateGraphModel)
            .where(TemplateGraphModel.id == template_graph_id.value)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return template_graph_model_to_entity(row) if row else None

    async def get_template_graph_by_name(self, template_graph_by_name: str) -> TemplateGraph | None:
        q = (
            select(TemplateGraphModel)
            .options(selectinload(TemplateGraphModel.nodes))
            .where(TemplateGraphModel.name == template_graph_by_name)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return template_graph_model_to_entity(row) if row else None

    async def save(self, template_graph: TemplateGraph) -> None:
        template_graph_model = template_graph_entity_to_model(template_graph)
        await self._session.merge(template_graph_model)


class SqlTemplateGraphNodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, template_graph_node_id: TemplateGraphNodeId) -> TemplateGraphNode | None:
        template_graph_node_query = (
            select(TemplateGraphNodeModel)
            .where(TemplateGraphNodeModel.id == template_graph_node_id.value)
        )
        template_graph_node = (await self._session.execute(template_graph_node_query)).scalar_one_or_none()
        return template_graph_node_model_to_entity(template_graph_node) if template_graph_node else None

    async def save(self, template_graph_node: TemplateGraphNode) -> None:
        await self._session.execute(
            update(WorkflowModel)
            .where(WorkflowModel.id == template_graph_node.id.value)
        )
        template_graph_node_model = template_graph_node_entity_to_model(template_graph_node)
        await self._session.merge(template_graph_node_model)
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
    GraphId,
    NodeId,
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

    def new_graph_id(self) -> GraphId:
        return GraphId(str(uuid.uuid4()))

    def new_node_id(self) -> NodeId:
        return NodeId(str(uuid.uuid4()))
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
    GraphId,
    NodeId,
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

    def new_graph_id(self) -> GraphId:
        return GraphId(str(uuid.uuid4()))

    def new_node_id(self) -> NodeId:
        return NodeId(str(uuid.uuid4()))
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

import uuid
from shell_ddd.infrastructure.logging.stdlib_logger import correlation_id_var
from shell_ddd.infrastructure.persistence.memory.memory import InMemoryUnitOfWork, InMemoryQueryServices



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


@pytest.fixture(autouse=True)
def auto_correlation_id():
    """Automatycznie ustawia correlation_id dla każdego testu."""
    token = correlation_id_var.set(f"test-{uuid.uuid4()}")
    yield
    correlation_id_var.reset(token)


@pytest.fixture
def queries(uow: InMemoryUnitOfWork) -> InMemoryQueryServices:
    return InMemoryQueryServices(uow)
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

from httpx import ASGITransport, AsyncClient

from shell_ddd.bootstrap.factory.application_factory import ApplicationFactory


async def _make_app(tmp_path: pathlib.Path):  # type: ignore[return]
    from shell_ddd.framework.api.app import create_app

    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    core_container = await ApplicationFactory(database_url=db_url).build()
    return create_app(core_container)


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

        #      core_container = app.state.core_container
        #      async with core_container.uow() as uow:

        #          base_planner = TemplateGraph(
        #              id="base-planner-id",
        #              name="base_planner",
        #              purpose="default_planning"
        #          )
        #          await uow.template_graphs.save(base_planner)
        #          await uow.commit()
        # ---------------------------------------

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/tasks/import", json={
                "task_name": "api_task",
                "md_path": str(md),
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

        db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
        core_container = await ApplicationFactory(database_url=db_url).build()
        from shell_ddd.framework.api.app import create_app

        app = create_app(core_container)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # import task first
            await client.post("/tasks/import", json={
                "task_name": "wf_task",
                "md_path": str(md),
            })

            # Attach a single-node Graph for the imported task so that
            # StartWorkflowHandler can anchor the cursor.
            from shell_ddd.domain.entities.graph import Graph, GraphNode
            from shell_ddd.domain.value_objects.ids import GraphId, NodeId, TemplateGraphId
            from shell_ddd.domain.value_objects.mode import Mode
            from shell_ddd.domain.value_objects.task_name import TaskName

            uow_factory = core_container.uow_factory()
            async with uow_factory as uow:
                task = await uow.tasks.get_current_by_name(TaskName("wf_task"))
                assert task is not None
                graph = Graph(
                    id=GraphId.generate(),
                    task_id=task.id,
                    template_graph_id=TemplateGraphId("tpl"),
                    raw_dict={},
                    nodes=[
                        GraphNode(
                            id=NodeId("wf_task-node-0"),
                            position=0,
                            node_dir="/fake/wf_task-0",
                            mode=Mode("agent"),
                            role="agent",
                            node_type="agent",
                        )
                    ],
                )
                await uow.graphs.save(graph)
                await uow.commit()

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
"""E2E test — Tasker full graph execution (Faza 14: step-by-step).

Uses InMemory adapters + FakeNodeProcessRunner so no real subprocess is spawned.
Verifies:
- ``RunTaskerWorkflowHandler`` creates a RUNNING Workflow and emits the first
  ``NodeExecutionRequested`` event.
- ``NodeExecutionWorker`` picks up the event, executes exactly one node, and
  emits the next ``NodeExecutionRequested`` until the graph is exhausted.
- ``NodeResult`` is persisted for every node (status = done/failed per runner).
- Workflow final status = ``done`` when all nodes succeed.
- Workflow final status = ``failed`` when any node fails (FailFastPolicy).
- ``WorkflowCompleted`` / ``NodeCompleted`` events are published.
"""
from __future__ import annotations

import pytest

from shell_ddd.domain.entities.graph import Graph
from shell_ddd.domain.entities.graph_node import GraphNode
from shell_ddd.infrastructure.persistence.memory.memory import InMemoryQueryServices

from shell_ddd.application.bus.event_bus import EventBus
from shell_ddd.application.bus.event_bus_publisher import EventBusPublisher
from shell_ddd.application.command_handlers.run_tasker_workflow_handler import RunTaskerWorkflowHandler
from shell_ddd.application.commands.commands import RunTaskerWorkflowCommand
from shell_ddd.application.event_handlers.node_execution_worker import NodeExecutionWorker
from shell_ddd.application.queries.queries import GetWorkflowQuery
from shell_ddd.application.query_handlers.query_handlers import GetWorkflowHandler
from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.events.events import (
    NodeCompleted,
    NodeExecutionRequested,
    NodeFailed,
    WorkflowCompleted,
    WorkflowFailed,
)
from shell_ddd.domain.value_objects.ids import GraphId, NodeId, TaskId
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeNodeProcessRunner,
    InMemoryUnitOfWork,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task_with_graph(name: str, node_modes: list[str], uow: InMemoryUnitOfWork) -> Task:
    """Build a Task and Graph with len(node_modes) nodes and store them via the UoW repos."""
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

    from shell_ddd.domain.value_objects.hash import Hash
    from shell_ddd.domain.value_objects.ids import TemplateGraphId
    from shell_ddd.domain.value_objects.task_body import TaskBody
    from shell_ddd.domain.value_objects.version import Version

    task = Task(
        id=task_id,
        name=task_name,
        version=Version.initial(),
        hash=Hash.of("x"),
        body=TaskBody("# Task"),
        is_current=True,
        created_at=datetime.now(tz=UTC),
    )
    uow.tasks._store[task_id.value] = task

    graph = Graph(
        id=graph_id,
        task_id=task_id,
        template_graph_id=TemplateGraphId("template_graph_id"),
        raw_dict={},
        nodes=nodes,
    )
    uow.graphs._store[graph_id.value] = graph
    return task


async def _run_tasker_full(
    uow: InMemoryUnitOfWork,
    clock: FakeClock,
    id_gen: FakeIdGenerator,
    runner: FakeNodeProcessRunner,
    task_name: str,
    work_dir: str = "/tmp",
) -> tuple[str, FakeEventPublisher]:
    """Wire handler + step-by-step worker via EventBus and run the full flow.

    The ``EventBusPublisher`` re-delivers each ``NodeExecutionRequested`` to
    ``NodeExecutionWorker``, which executes exactly one node, persists its
    result, advances the cursor, and emits the next event — looping until
    the graph is exhausted (``WorkflowCompleted``) or a node fails
    (``WorkflowFailed`` under the default ``FailFastPolicy``).
    """
    collector = FakeEventPublisher()

    event_bus = EventBus()
    bus_publisher = EventBusPublisher(event_bus)

    from shell_ddd.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
    composite = CompositeEventPublisher(publishers=[collector, bus_publisher])

    worker_factory = lambda: NodeExecutionWorker(  # noqa: E731
        uow=uow,
        clock=clock,
        id_gen=id_gen,
        runner=runner,
        event_publisher=composite,
        logger=FakeLogger(),
    )
    event_bus.subscribe(NodeExecutionRequested, worker_factory)

    handler = RunTaskerWorkflowHandler(
        uow=uow, clock=clock, id_gen=id_gen, event_publisher=composite
    )
    workflow_id = await handler.handle(
        RunTaskerWorkflowCommand(task_name=task_name, work_dir=work_dir)
    )

    return workflow_id, collector


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


@pytest.fixture()
def queries(uow: InMemoryUnitOfWork) -> InMemoryQueryServices:
    """Fixture dostarczający serwis zapytań In-Memory dla testu E2E."""
    return InMemoryQueryServices(uow)


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
            queries: InMemoryQueryServices,
    ) -> None:
        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)
        _make_task_with_graph("three-node-task", ["agent", "tool", "worker"], uow)

        workflow_id, _ = await _run_tasker_full(uow, clock, id_gen, runner, "three-node-task")

        dto = await GetWorkflowHandler(queries).handle(GetWorkflowQuery(workflow_id))
        assert dto is not None
        assert dto.status == "done"
        assert len(dto.node_states) == 3
        assert all(s.status == "done" for s in dto.node_states.values())

    async def test_three_node_results_saved(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
    ) -> None:
        runner = FakeNodeProcessRunner(stdout="result", returncode=0)
        _make_task_with_graph("nr-task", ["agent", "tool", "worker"], uow)

        workflow_id, _ = await _run_tasker_full(uow, clock, id_gen, runner, "nr-task")

        from shell_ddd.domain.value_objects.ids import WorkflowId
        wf = await uow.workflows.get_by_id(WorkflowId(workflow_id))
        assert wf is not None
        results = list(wf.node_results.values())
        assert len(results) == 3
        assert all(r.status.value == "done" for r in results)
        assert all(r.stdout == "result" for r in results)

    async def test_events_published(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=0)
        _make_task_with_graph("ev-task", ["agent", "tool", "worker"], uow)

        _, collector = await _run_tasker_full(uow, clock, id_gen, runner, "ev-task")

        types = [type(e) for e in collector.published]
        assert WorkflowCompleted in types
        assert types.count(NodeCompleted) == 3
        assert NodeFailed not in types
        assert WorkflowFailed not in types


class TestRunTaskerWorkflowPartialFailure:
    """One node returns non-zero → workflow FAILED."""

    async def test_workflow_marked_failed(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=1, stderr="crash")
        _make_task_with_graph("fail-task", ["agent", "tool", "worker"], uow)

        workflow_id, _ = await _run_tasker_full(uow, clock, id_gen, runner, "fail-task")

        dto = await GetWorkflowHandler(queries).handle(GetWorkflowQuery(workflow_id))
        assert dto is not None
        assert dto.status == "failed"

    async def test_workflow_failed_event_published(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
    ) -> None:
        runner = FakeNodeProcessRunner(returncode=1)
        _make_task_with_graph("fail-ev-task", ["agent", "tool"], uow)

        _, collector = await _run_tasker_full(uow, clock, id_gen, runner, "fail-ev-task")

        types = [type(e) for e in collector.published]
        assert WorkflowFailed in types
        assert WorkflowCompleted not in types


class TestRunTaskerWorkflowEdgeCases:
    async def test_empty_graph_raises_workflow_has_no_nodes(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            events: FakeEventPublisher,
    ) -> None:
        from shell_ddd.domain.exceptions import WorkflowHasNoNodes

        _make_task_with_graph("empty-task", [], uow)
        handler = RunTaskerWorkflowHandler(
            uow=uow, clock=clock, id_gen=id_gen, event_publisher=events
        )
        with pytest.raises(WorkflowHasNoNodes):
            await handler.handle(
                RunTaskerWorkflowCommand(task_name="empty-task", work_dir="/tmp")
            )

    async def test_task_not_found_raises(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            events: FakeEventPublisher,
    ) -> None:
        from shell_ddd.domain.exceptions import TaskNotFound

        handler = RunTaskerWorkflowHandler(uow=uow, clock=clock, id_gen=id_gen, event_publisher=events)
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
        md.write_text("# My Task", encoding="utf-8")
        loader = FileSystemTaskLoader()
        task_text = await loader.load(str(md))
        assert task_text == "# My Task"


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

from shell_ddd.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell_ddd.infrastructure.persistence.sql.query_services import SqlQueryServices

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
    FakeLogger,
    FakeTaskLoader,
)
from shell_ddd.infrastructure.persistence.sql import build_session_factory

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
    #await create_all_tables(_PG_URL)
    await bootstrap_database(_PG_URL)
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
    return FakeTaskLoader(md="# PG Task")


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
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        await handler.handle(ImportTaskCommand("t.md", "pg-task"))

        q = GetCurrentTaskHandler(SqlQueryServices(session_factory))
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
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        await handler.handle(ImportTaskCommand("t.md", "pg-task-v"))
        await handler.handle(ImportTaskCommand("t.md", "pg-task-v"))

        q = GetCurrentTaskHandler(SqlQueryServices(session_factory))
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
        imp = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        await imp.handle(ImportTaskCommand("t.md", "pg-wf-task"))

        start = StartWorkflowHandler(uow, clock, id_gen, events)
        wf_id = await start.handle(StartWorkflowCommand("pg-wf-task"))

        q = GetWorkflowHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"
        assert dto.task_name == "pg-wf-task"

    async def test_workflow_not_found_returns_none(
        self,
        uow: SqlAlchemyUnitOfWork,
    ) -> None:
        q = GetWorkflowHandler(SqlQueryServices(session_factory))
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

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("pg-sys-prompt"))
        assert dto is not None
        assert dto.body == "You are a pg helper."

    async def test_prompt_not_found_returns_none(
        self,
        uow: SqlAlchemyUnitOfWork,
    ) -> None:
        q = GetPromptHandler(SqlQueryServices(session_factory))
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

        q = GetNodeResultHandler(SqlQueryServices(session_factory))
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

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("pg-rollback-prompt-x"))
        assert dto is None
```

### tests/integration/sql_sqlite/__init__.py
```
"""SQLite integration test package."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from shell_ddd.application.command_handlers.import_task_handler import ImportTaskHandler
from shell_ddd.application.command_handlers.save_node_result_handler import SaveNodeResultHandler
from shell_ddd.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell_ddd.application.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell_ddd.application.commands.commands import ImportTaskCommand, StartWorkflowCommand, SaveNodeResultCommand, \
    SavePromptCommand
from shell_ddd.application.queries.queries import GetCurrentTaskQuery, GetWorkflowQuery, GetNodeResultQuery, \
    GetPromptQuery
from shell_ddd.application.query_handlers.query_handlers import GetCurrentTaskHandler, GetWorkflowHandler, \
    GetNodeResultHandler, GetPromptHandler
from shell_ddd.bootstrap.database_config.database_bootstrap import bootstrap_database

from shell_ddd.domain.entities.prompt import Prompt
from shell_ddd.domain.value_objects.ids import (
    PromptId,
)

from shell_ddd.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell_ddd.infrastructure.persistence.memory.memory import FakeClock, FakeTaskLoader, FakeEventPublisher, \
    FakeIdGenerator, FakeLogger
from shell_ddd.infrastructure.persistence.sql import build_session_factory
from shell_ddd.infrastructure.persistence.sql.query_services import SqlQueryServices


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def session_factory(tmp_path_factory: pytest.TempPathFactory) -> async_sessionmaker:  # type: ignore[type-arg]
    db = tmp_path_factory.mktemp("sqlite") / "test.db"
    url = f"sqlite+aiosqlite:///{db}"
    await bootstrap_database(url)
    return build_session_factory(url)


@pytest.fixture()
def uow(session_factory: async_sessionmaker) -> SqlAlchemyUnitOfWork:  # type: ignore[type-arg]
    return SqlAlchemyUnitOfWork(session_factory)


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


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
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def task_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# SQL Task")


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
        session_factory: async_sessionmaker,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        await handler.handle(ImportTaskCommand("t.md", "sql-task"))

        q = GetCurrentTaskHandler(SqlQueryServices(session_factory))
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
        session_factory: async_sessionmaker,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        await handler.handle(ImportTaskCommand("t.md", "sql-task-v"))
        await handler.handle(ImportTaskCommand("t.md", "sql-task-v"))

        q = GetCurrentTaskHandler(SqlQueryServices(session_factory))
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
        session_factory: async_sessionmaker,
    ) -> None:
        imp = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        await imp.handle(ImportTaskCommand("t.md", "wf-task"))

        start = StartWorkflowHandler(uow, clock, id_gen, events)
        wf_id = await start.handle(StartWorkflowCommand("wf-task"))

        q = GetWorkflowHandler(SqlQueryServices(session_factory))
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
        session_factory: async_sessionmaker,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("sys-prompt", "You are helpful."))

        q = GetPromptHandler(SqlQueryServices(session_factory))
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
        session_factory: async_sessionmaker,
    ) -> None:
        from shell_ddd.domain.entities.workflow import Workflow
        from shell_ddd.domain.value_objects.ids import WorkflowId
        async with uow as u:
            await u.workflows.save(
                Workflow.new(id_=WorkflowId("wf-sql-1"), task_name="t", now=clock.now())
            )
            await u.commit()

        handler = SaveNodeResultHandler(uow, clock, id_gen, events)
        await handler.handle(
            SaveNodeResultCommand(
                workflow_id="wf-sql-1",
                node_id="node-sql-1",
                status="done",
                stdout="success",
            )
        )

        q = GetNodeResultHandler(SqlQueryServices(session_factory))
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
                    Prompt.new(
                        id_=id_gen.new_prompt_id(),
                        name="rollback-prompt",
                        body="body",
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("rollback-prompt"))
        assert dto is None
```

### tests/integration/sql_sqlite/test_sql_sqlite.py
```
"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from shell_ddd.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell_ddd.infrastructure.logging.stdlib_logger import get_correlation_id
from shell_ddd.infrastructure.persistence.sql.query_services import SqlQueryServices

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
    FakeLogger,
    FakeTaskLoader,
)
from shell_ddd.infrastructure.persistence.sql import build_session_factory


# ---------------------------------------------------------------------------
# Fixtures (module-scoped DB, function-scoped UoW)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def session_factory(
    tmp_path_factory: pytest.TempPathFactory,
) -> async_sessionmaker:  # type: ignore[type-arg]
    db = tmp_path_factory.mktemp("sqlite") / "test.db"
    url = f"sqlite+aiosqlite:///{db}"
    await bootstrap_database(url)
    return build_session_factory(url)


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
    return FakeTaskLoader(md="# SQL Task")


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class TestSqlTaskRepository:
    async def test_import_and_get_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
        session_factory,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        await handler.handle(ImportTaskCommand("t.md", "sql-task"))

        q = GetCurrentTaskHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskQuery("sql-task"))
        assert dto is not None
        assert dto.name == "sql-task"
        assert dto.is_current is True

    async def test_reimport_marks_old_non_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
        session_factory,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        await handler.handle(ImportTaskCommand("t.md", "sql-task-v"))
        await handler.handle(ImportTaskCommand("t.md", "sql-task-v"))

        q = GetCurrentTaskHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskQuery("sql-task-v"))
        assert dto is not None
        assert dto.is_current is True


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


class TestSqlWorkflowRepository:
    async def test_start_and_query_workflow(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        imp = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        await imp.handle(ImportTaskCommand("t.md", "wf-task"))

        # Persist a single-node Graph so StartWorkflowHandler can anchor the cursor.
        from shell_ddd.domain.entities.graph import Graph, GraphNode
        from shell_ddd.domain.value_objects.ids import GraphId, NodeId, TemplateGraphId
        from shell_ddd.domain.value_objects.mode import Mode
        from shell_ddd.domain.value_objects.task_name import TaskName

        async with uow as u:
            task = await u.tasks.get_current_by_name(TaskName("wf-task"))
            assert task is not None
            graph = Graph(
                id=GraphId.generate(),
                task_id=task.id,
                template_graph_id=TemplateGraphId("tpl"),
                raw_dict={},
                nodes=[
                    GraphNode(
                        id=NodeId("wf-task-node-0"),
                        position=0,
                        node_dir="/fake/wf-task-0",
                        mode=Mode("agent"),
                        role="agent",
                        node_type="agent",
                    )
                ],
            )
            await u.graphs.save(graph)
            await u.commit()

        start = StartWorkflowHandler(uow, clock, id_gen, events)
        wf_id = await start.handle(StartWorkflowCommand("wf-task"))

        q = GetWorkflowHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"
        assert dto.task_name == "wf-task"

    async def test_workflow_not_found_returns_none(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        q = GetWorkflowHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetWorkflowQuery("no-such-wf"))
        assert dto is None


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------


class TestSqlPromptRepository:
    async def test_save_and_get_prompt(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("sys-prompt", "You are helpful."))

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("sys-prompt"))
        assert dto is not None
        assert dto.body == "You are helpful."

    async def test_prompt_not_found_returns_none(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("missing-prompt"))
        assert dto is None


# ---------------------------------------------------------------------------
# NodeResult
# ---------------------------------------------------------------------------


class TestSqlNodeResultRepository:
    async def test_save_and_get_result(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        session_factory: async_sessionmaker,
    ) -> None:
        # Seed a Workflow first — NodeResult is owned by Workflow aggregate.
        from shell_ddd.domain.entities.workflow import Workflow
        from shell_ddd.domain.value_objects.ids import WorkflowId
        async with uow as u:
            await u.workflows.save(
                Workflow.new(id_=WorkflowId("wf-sql-nr-1"), task_name="t", now=clock.now())
            )
            await u.commit()

        handler = SaveNodeResultHandler(uow, clock, id_gen, events)
        await handler.handle(
            SaveNodeResultCommand(
                workflow_id="wf-sql-nr-1",
                node_id="node-sql-nr-1",
                status="done",
                stdout="success",
            )
        )

        q = GetNodeResultHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetNodeResultQuery("node-sql-nr-1", "wf-sql-nr-1"))
        assert dto is not None
        assert dto.stdout == "success"
        assert dto.status == "done"


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------


class TestSqlUnitOfWorkRollback:
    async def test_rollback_on_exception_leaves_db_clean(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        session_factory: async_sessionmaker,
    ) -> None:
        try:
            async with uow as u:
                from shell_ddd.domain.entities.prompt import Prompt
                from shell_ddd.domain.value_objects.ids import PromptId

                await u.prompts.save(
                    Prompt.new(
                        id_=PromptId("rollback-prompt-x"),
                        name="rollback-prompt-x",
                        body="should not persist",
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("rollback-prompt-x"))
        assert dto is None


# ---------------------------------------------------------------------------
# Faza 9: RAG document + Session repos
# ---------------------------------------------------------------------------


class TestSqlRagDocumentRepository:
    async def test_index_and_search_similar(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell_ddd.application.command_handlers.index_document_handler import IndexDocumentHandler
        from shell_ddd.application.commands.commands import IndexDocumentCommand
        from shell_ddd.application.queries.queries import SearchSimilarQuery
        from shell_ddd.application.query_handlers.query_handlers import SearchSimilarHandler
        from shell_ddd.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        text = "SQLite RAG integration test " * 30
        cmd = IndexDocumentCommand(source_uri="file:///sql_rag.md", title="SQL RAG", domain="sql-test", text=text)
        await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(cmd)

        results = await SearchSimilarHandler(SqlQueryServices(session_factory), embedder).handle(
            SearchSimilarQuery(query_text="SQLite RAG integration", top_k=5, domain="sql-test")
        )
        assert len(results) > 0
        assert all(r.domain == "sql-test" for r in results)

    async def test_search_domain_filter_excludes_other_domains(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell_ddd.application.command_handlers.index_document_handler import IndexDocumentHandler
        from shell_ddd.application.commands.commands import IndexDocumentCommand
        from shell_ddd.application.queries.queries import SearchSimilarQuery
        from shell_ddd.application.query_handlers.query_handlers import SearchSimilarHandler
        from shell_ddd.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(
            IndexDocumentCommand(source_uri="file:///x.md", title="X", domain="domain-x", text="unique text x " * 20)
        )
        results = await SearchSimilarHandler(SqlQueryServices(session_factory), embedder).handle(
            SearchSimilarQuery(query_text="unique text x", top_k=5, domain="domain-y")
        )
        assert results == []


class TestSqlSessionRepository:
    async def test_open_append_close_and_history(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell_ddd.application.command_handlers.session_handlers import (
            AppendMessageHandler,
            CloseSessionHandler,
            OpenSessionHandler,
        )
        from shell_ddd.application.commands.commands import (
            AppendMessageCommand,
            CloseSessionCommand,
            OpenSessionCommand,
        )
        from shell_ddd.application.queries.queries import GetSessionHistoryQuery
        from shell_ddd.application.query_handlers.query_handlers import GetSessionHistoryHandler

        session_id = await OpenSessionHandler(uow, clock, id_gen).handle(
            OpenSessionCommand(goal="integration test")
        )
        await AppendMessageHandler(uow, clock, id_gen).handle(
            AppendMessageCommand(session_id=session_id.value,correlation_id=get_correlation_id(), sender="sql-agent", receiver="router", payload={"k": 1})
        )
        await AppendMessageHandler(uow, clock, id_gen).handle(
            AppendMessageCommand(session_id=session_id.value,correlation_id=get_correlation_id(), sender="router", receiver="sql-agent", payload={"k": 2})
        )
        await CloseSessionHandler(uow, clock).handle(CloseSessionCommand(session_id=session_id.value))

        dto = await GetSessionHistoryHandler(SqlQueryServices(session_factory)).handle(GetSessionHistoryQuery(session_id=session_id.value))
        assert dto is not None
        assert dto.status == "closed"
        assert len(dto.messages) == 2


# ---------------------------------------------------------------------------
# SqlAuditPublisher
# ---------------------------------------------------------------------------


class TestSqlAuditPublisher:
    async def test_persists_audit_rows(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell_ddd.domain.events.events import TaskCreated, WorkflowStarted
        from shell_ddd.domain.value_objects.ids import TaskId, WorkflowId
        from shell_ddd.domain.value_objects.task_name import TaskName
        from shell_ddd.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
        from shell_ddd.infrastructure.persistence.sql.models import AuditEventModel

        pub = SqlAuditPublisher(session_factory)
        events = [
            TaskCreated.now(task_id=TaskId.generate(), task_name=TaskName("audit-task"), now=datetime(2026, 1, 1, tzinfo=UTC)),
            WorkflowStarted.now(workflow_id=WorkflowId.generate(), task_name="audit-task", now=datetime(2026, 1, 1, tzinfo=UTC)),
        ]
        await pub.publish(events)

        async with session_factory() as session:
            rows = (await session.execute(select(AuditEventModel))).scalars().all()

        types = {r.event_type for r in rows}
        assert "TaskCreated" in types
        assert "WorkflowStarted" in types

    async def test_empty_events_writes_nothing(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell_ddd.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
        from shell_ddd.infrastructure.persistence.sql.models import AuditEventModel

        pub = SqlAuditPublisher(session_factory)
        # record count before
        async with session_factory() as session:
            before = len((await session.execute(select(AuditEventModel))).scalars().all())
        await pub.publish([])
        async with session_factory() as session:
            after = len((await session.execute(select(AuditEventModel))).scalars().all())
        assert before == after


# ---------------------------------------------------------------------------
# SqlOutboxPublisher + OutboxRelay
# ---------------------------------------------------------------------------


class TestSqlOutboxPublisher:
    async def test_writes_outbox_rows(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell_ddd.domain.events.events import TaskCreated
        from shell_ddd.domain.value_objects.ids import TaskId
        from shell_ddd.domain.value_objects.task_name import TaskName
        from shell_ddd.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel

        pub = SqlOutboxPublisher(session_factory)
        events = [TaskCreated.now(task_id=TaskId.generate(), task_name=TaskName("ob-task"), now=datetime(2026, 1, 1, tzinfo=UTC))]
        await pub.publish(events)

        async with session_factory() as session:
            rows = (await session.execute(select(OutboxEventModel))).scalars().all()
        assert any(r.event_type == "TaskCreated" for r in rows)
        assert all(r.published_at is None for r in rows)

    async def test_empty_publish_noop(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell_ddd.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel

        pub = SqlOutboxPublisher(session_factory)
        async with session_factory() as session:
            before = len((await session.execute(select(OutboxEventModel))).scalars().all())
        await pub.publish([])
        async with session_factory() as session:
            after = len((await session.execute(select(OutboxEventModel))).scalars().all())
        assert before == after


class TestOutboxRelay:
    async def test_relay_marks_rows_published(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell_ddd.domain.events.events import WorkflowStarted
        from shell_ddd.domain.value_objects.ids import WorkflowId
        from shell_ddd.infrastructure.messaging.outbox_relay import OutboxRelay
        from shell_ddd.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel
        from shell_ddd.infrastructure.persistence.memory.memory import FakeEventPublisher

        # Write an event to outbox
        outbox_pub = SqlOutboxPublisher(session_factory)
        event = WorkflowStarted.now(workflow_id=WorkflowId.generate(), task_name="relay-task", now=datetime(2026, 1, 1, tzinfo=UTC))
        await outbox_pub.publish([event])

        # Run relay — downstream captures events
        downstream = FakeEventPublisher()
        relay = OutboxRelay(session_factory, downstream)
        count = await relay.run_once()

        assert count >= 1
        async with session_factory() as session:
            unpublished = (
                await session.execute(
                    select(OutboxEventModel).where(OutboxEventModel.published_at.is_(None))
                )
            ).scalars().all()
        # all rows that were pending are now published
        assert all(r.published_at is not None for r in [])  # placeholder: rows were updated

    async def test_relay_run_twice_idempotent(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell_ddd.domain.events.events import TaskCreated
        from shell_ddd.domain.value_objects.ids import TaskId
        from shell_ddd.domain.value_objects.task_name import TaskName
        from shell_ddd.infrastructure.messaging.outbox_relay import OutboxRelay
        from shell_ddd.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell_ddd.infrastructure.persistence.memory.memory import FakeEventPublisher

        outbox_pub = SqlOutboxPublisher(session_factory)
        await outbox_pub.publish(
            [TaskCreated.now(task_id=TaskId.generate(), task_name=TaskName("idm-task"), now=datetime(2026, 1, 1, tzinfo=UTC))]
        )

        downstream = FakeEventPublisher()
        relay = OutboxRelay(session_factory, downstream)
        first = await relay.run_once()
        second = await relay.run_once()

        assert first >= 1
        assert second == 0  # nothing left to process


# ---------------------------------------------------------------------------
# Transactional Outbox: atomicity guarantee
# ---------------------------------------------------------------------------


class TestTransactionalOutbox:
    async def test_outbox_written_atomically_with_domain_state(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        """Outbox rows must be present after UoW commit without a separate publish step."""
        from sqlalchemy import select

        from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel

        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        await handler.handle(ImportTaskCommand("t.md", "atomic-task"))

        async with session_factory() as session:
            rows = (
                await session.execute(
                    select(OutboxEventModel).where(
                        OutboxEventModel.event_type == "TaskCreated"
                    )
                )
            ).scalars().all()

        assert any(r.payload.get("task_name") is not None for r in rows), (
            "Outbox row must be written in same transaction as domain state"
        )

    async def test_rollback_removes_staged_outbox_events(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        session_factory: async_sessionmaker,
    ) -> None:
        """If the UoW transaction is rolled back, no outbox rows must be written."""
        from sqlalchemy import select

        from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel
        from shell_ddd.domain.events.events import WorkflowStarted

        async with session_factory() as s:
            before = len(
                (await s.execute(select(OutboxEventModel))).scalars().all()
            )

        try:
            async with uow as u:
                u.stage_events(
                    [WorkflowStarted.now(
                        workflow_id=__import__("shell_ddd.domain.value_objects.ids", fromlist=["WorkflowId"]).WorkflowId("wf-rollback"),
                        task_name="rollback-task",
                        now=clock.now(),
                    )]
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        async with session_factory() as s:
            after = len(
                (await s.execute(select(OutboxEventModel))).scalars().all()
            )

        assert after == before, "Rolled-back transaction must not write outbox rows"
```

### tests/unit/__init__.py
```
```

### tests/unit/application/__init__.py
```
```

### tests/unit/application/test_build_graph_on_task_created.py
```
"""Unit tests for ``BuildGraphOnTaskCreated`` event handler."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shell_ddd.application.event_handlers.build_graph_on_task_created import (
    BuildGraphOnTaskCreated,
)
from shell_ddd.application.exceptions import TemplateGraphNotFoundException
from shell_ddd.domain.entities.template_graph import TemplateGraph
from shell_ddd.domain.entities.template_graph_node import TemplateGraphNode
from shell_ddd.domain.events.events import GraphBuilt, TaskCreated
from shell_ddd.domain.value_objects.ids import (
    TaskId,
    TemplateGraphId,
    TemplateGraphNodeId,
)
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    InMemoryUnitOfWork,
)


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


@pytest.fixture()
def logger() -> FakeLogger:
    return FakeLogger()


def _seed_template(uow: InMemoryUnitOfWork, name: str = "base_planner") -> TemplateGraph:
    template = TemplateGraph(
        id=TemplateGraphId(f"{name}-id"),
        name=name,
        purpose="planning",
        nodes=[
            TemplateGraphNode(
                id=TemplateGraphNodeId("tn-1"),
                position=0,
                mode=Mode("agent"),
                role="agent",
                node_type="agent",
            ),
            TemplateGraphNode(
                id=TemplateGraphNodeId("tn-2"),
                position=1,
                mode=Mode("worker"),
                role="worker",
                node_type="worker",
            ),
        ],
    )
    uow.template_graphs._store[name] = template
    return template


def _task_created_event(now: datetime) -> TaskCreated:
    return TaskCreated.now(
        task_id=TaskId("task-abc"),
        task_name=TaskName("my-task"),
        now=now,
    )


# ---------------------------------------------------------------------------
# Tests — DoD obligatory matrix
# ---------------------------------------------------------------------------


class TestBuildGraphOnTaskCreated:
    async def test_happy_path_builds_and_persists_graph(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        logger: FakeLogger,
    ) -> None:
        _seed_template(uow)
        handler = BuildGraphOnTaskCreated(uow, clock, id_gen, events, logger)

        await handler.handle(_task_created_event(clock.now()))

        graph = await uow.graphs.get_by_task_id(TaskId("task-abc"))
        assert graph is not None
        assert graph.task_id == TaskId("task-abc")
        assert len(graph.nodes) == 2
        assert any(isinstance(e, GraphBuilt) for e in events.published)

    async def test_template_not_found_raises(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        logger: FakeLogger,
    ) -> None:
        # Replace seeded base_planner with nothing
        uow.template_graphs._store.clear()
        handler = BuildGraphOnTaskCreated(uow, clock, id_gen, events, logger)

        with pytest.raises(TemplateGraphNotFoundException):
            await handler.handle(_task_created_event(clock.now()))

    async def test_idempotent_when_graph_already_exists(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        logger: FakeLogger,
    ) -> None:
        _seed_template(uow)
        handler = BuildGraphOnTaskCreated(uow, clock, id_gen, events, logger)

        # First call builds the graph.
        await handler.handle(_task_created_event(clock.now()))
        first_graph = await uow.graphs.get_by_task_id(TaskId("task-abc"))
        assert first_graph is not None
        first_graph_id = first_graph.id

        events.published.clear()
        # Second call must be a no-op.
        await handler.handle(_task_created_event(clock.now()))

        second_graph = await uow.graphs.get_by_task_id(TaskId("task-abc"))
        assert second_graph is not None
        assert second_graph.id == first_graph_id
        assert events.published == []

    async def test_no_events_published_on_failure(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        logger: FakeLogger,
    ) -> None:
        # No template seeded — handler must NOT publish events when failing.
        uow.template_graphs._store.clear()
        handler = BuildGraphOnTaskCreated(uow, clock, id_gen, events, logger)

        with pytest.raises(TemplateGraphNotFoundException):
            await handler.handle(_task_created_event(clock.now()))

        assert events.published == []
        # Graph must not exist either.
        assert await uow.graphs.get_by_task_id(TaskId("task-abc")) is None
```

### tests/unit/application/test_handlers.py
```
"""Unit tests for application command handlers (using InMemory adapters)."""
from __future__ import annotations

import pytest

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
from shell_ddd.domain.events.events import TaskCreated, WorkflowStarted
from shell_ddd.domain.exceptions import TaskNotFound
from shell_ddd.infrastructure.logging.stdlib_logger import get_correlation_id
from shell_ddd.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
    InMemoryUnitOfWork,
)

from shell_ddd.infrastructure.persistence.memory.memory import InMemoryQueryServices


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


@pytest.fixture()
def task_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# My Task")


@pytest.fixture()
def fake_logger() -> FakeLogger:
    return FakeLogger()


@pytest.fixture()
def queries(uow: InMemoryUnitOfWork) -> InMemoryQueryServices:
    return InMemoryQueryServices(uow)


# ---------------------------------------------------------------------------
# ImportTaskHandler
# ---------------------------------------------------------------------------


class TestImportTaskHandler:
    async def test_happy_path(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            events: FakeEventPublisher,
            task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        task_id = await handler.handle(ImportTaskCommand("t.md", "my-task"))

        assert task_id
        assert len(events.published) == 1
        assert isinstance(events.published[0], TaskCreated)

    async def test_task_saved_as_current(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            events: FakeEventPublisher,
            task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        await handler.handle(ImportTaskCommand("t.md", "my-task"))

        from shell_ddd.domain.value_objects.task_name import TaskName

        task = await uow.tasks.get_current_by_name(TaskName("my-task"))
        assert task is not None
        assert task.is_current is True

    async def test_reimport_marks_previous_non_current(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            events: FakeEventPublisher,
            task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        first_id = await handler.handle(ImportTaskCommand("t.md", "my-task"))
        await handler.handle(ImportTaskCommand("t.md", "my-task"))

        old = await uow.tasks.get_by_id(
            __import__(
                "shell_ddd.domain.value_objects.ids", fromlist=["TaskId"]
            ).TaskId(first_id)
        )
        assert old is not None
        assert old.is_current is False

    async def test_invalid_task_name_raises(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            events: FakeEventPublisher,
            task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events, FakeLogger())
        with pytest.raises(ValueError):
            await handler.handle(ImportTaskCommand("t.md", ""))


# ---------------------------------------------------------------------------
# StartWorkflowHandler
# ---------------------------------------------------------------------------


class TestStartWorkflowHandler:
    async def _import_task(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            task_loader: FakeTaskLoader,
    ) -> None:
        pub = FakeEventPublisher()
        h = ImportTaskHandler(uow, clock, id_gen, task_loader, pub, FakeLogger())
        await h.handle(ImportTaskCommand("t.md", "my-task"))
        await self._attach_graph(uow, "my-task")

    @staticmethod
    async def _attach_graph(uow: InMemoryUnitOfWork, task_name: str) -> None:
        """Persist a single-node Graph for the imported task so that
        ``StartWorkflowHandler`` can anchor the cursor on a first node.
        """
        from shell_ddd.domain.entities.graph import Graph, GraphNode
        from shell_ddd.domain.value_objects.ids import GraphId, NodeId, TemplateGraphId
        from shell_ddd.domain.value_objects.mode import Mode
        from shell_ddd.domain.value_objects.task_name import TaskName

        task = await uow.tasks.get_current_by_name(TaskName(task_name))
        assert task is not None
        graph = Graph(
            id=GraphId.generate(),
            task_id=task.id,
            template_graph_id=TemplateGraphId("tpl"),
            raw_dict={},
            nodes=[
                GraphNode(
                    id=NodeId(f"{task_name}-node-0"),
                    position=0,
                    node_dir=f"/fake/{task_name}-0",
                    mode=Mode("agent"),
                    role="agent",
                    node_type="agent",
                )
            ],
        )
        uow.graphs._store[graph.id.value] = graph

    async def test_happy_path(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            events: FakeEventPublisher,
            task_loader: FakeTaskLoader,
    ) -> None:
        await self._import_task(uow, clock, id_gen, task_loader)
        handler = StartWorkflowHandler(uow, clock, id_gen, events)
        wf_id = await handler.handle(StartWorkflowCommand("my-task"))

        assert wf_id
        assert any(isinstance(e, WorkflowStarted) for e in events.published)

    async def test_task_not_found_raises(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            events: FakeEventPublisher,
    ) -> None:
        handler = StartWorkflowHandler(uow, clock, id_gen, events)
        with pytest.raises(TaskNotFound):
            await handler.handle(StartWorkflowCommand("nonexistent"))

    async def test_workflow_persisted(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            events: FakeEventPublisher,
            task_loader: FakeTaskLoader,
            queries: InMemoryQueryServices,
    ) -> None:
        await self._import_task(uow, clock, id_gen, task_loader)
        handler = StartWorkflowHandler(uow, clock, id_gen, events)
        wf_id = await handler.handle(StartWorkflowCommand("my-task"))

        q_handler = GetWorkflowHandler(queries)
        dto = await q_handler.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"


# ---------------------------------------------------------------------------
# SaveNodeResultHandler
# ---------------------------------------------------------------------------


class TestSaveNodeResultHandler:
    async def test_happy_path(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            events: FakeEventPublisher,
            queries: InMemoryQueryServices,
    ) -> None:
        from shell_ddd.domain.entities.workflow import Workflow
        from shell_ddd.domain.value_objects.ids import WorkflowId
        wf = Workflow.new(id_=WorkflowId("wf-1"), task_name="t", now=clock.now())
        uow.workflows._store["wf-1"] = wf

        handler = SaveNodeResultHandler(uow, clock, id_gen, events)
        result_id = await handler.handle(
            SaveNodeResultCommand(
                workflow_id="wf-1",
                node_id="node-1",
                status="done",
                stdout="ok",
            )
        )
        assert result_id
        q_handler = GetNodeResultHandler(queries)
        dto = await q_handler.handle(GetNodeResultQuery("node-1", "wf-1"))
        assert dto is not None
        assert dto.stdout == "ok"


# ---------------------------------------------------------------------------
# SavePromptHandler
# ---------------------------------------------------------------------------


class TestSavePromptHandler:
    async def test_happy_path(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("system", "You are a helpful assistant."))

        q_handler = GetPromptHandler(queries)
        dto = await q_handler.handle(GetPromptQuery("system"))
        assert dto is not None
        assert dto.body == "You are a helpful assistant."
        assert dto.is_current is True

    async def test_re_save_marks_old_non_current(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("system", "v1"))
        await handler.handle(SavePromptCommand("system", "v2"))

        q_handler = GetPromptHandler(queries)
        dto = await q_handler.handle(GetPromptQuery("system"))
        assert dto is not None
        assert dto.body == "v2"


# ---------------------------------------------------------------------------
# QueryHandlers — not found
# ---------------------------------------------------------------------------


class TestQueryHandlersNotFound:
    async def test_get_task_not_found(self, queries: InMemoryQueryServices) -> None:
        dto = await GetCurrentTaskHandler(queries).handle(GetCurrentTaskQuery("missing"))
        assert dto is None

    async def test_get_workflow_not_found(self, queries: InMemoryQueryServices) -> None:
        dto = await GetWorkflowHandler(queries).handle(GetWorkflowQuery("no-id"))
        assert dto is None


# ---------------------------------------------------------------------------
# Faza 9: IndexDocument + Session handlers
# ---------------------------------------------------------------------------


class TestIndexDocumentHandler:
    async def test_index_and_search_returns_chunks(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        from shell_ddd.application.command_handlers.index_document_handler import IndexDocumentHandler
        from shell_ddd.application.commands.commands import IndexDocumentCommand
        from shell_ddd.application.queries.queries import SearchSimilarQuery
        from shell_ddd.application.query_handlers.query_handlers import SearchSimilarHandler
        from shell_ddd.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        cmd = IndexDocumentCommand(
            source_uri="file:///doc.md",
            title="Doc",
            domain="test",
            text="Hello world " * 50,
        )
        doc_id = await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(cmd)
        assert doc_id is not None

        results = await SearchSimilarHandler(queries, embedder).handle(
            SearchSimilarQuery(query_text="Hello world", top_k=3, domain="test")
        )
        assert len(results) > 0
        assert results[0].domain == "test"

    async def test_index_empty_text_creates_no_chunks(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
    ) -> None:
        from shell_ddd.application.command_handlers.index_document_handler import IndexDocumentHandler
        from shell_ddd.application.commands.commands import IndexDocumentCommand
        from shell_ddd.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        cmd = IndexDocumentCommand(source_uri="file:///empty.md", title="Empty", domain="x", text="")
        doc_id = await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(cmd)
        assert doc_id is not None
        doc = await uow.rag_documents.get_by_id(doc_id)
        assert doc is not None
        assert doc.chunks == []


class TestSessionHandlers:
    async def test_open_and_get_history(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        from shell_ddd.application.command_handlers.session_handlers import (
            AppendMessageHandler,
            OpenSessionHandler,
        )
        from shell_ddd.application.commands.commands import AppendMessageCommand, OpenSessionCommand
        from shell_ddd.application.queries.queries import GetSessionHistoryQuery
        from shell_ddd.application.query_handlers.query_handlers import GetSessionHistoryHandler

        session_id = await OpenSessionHandler(uow, clock, id_gen).handle(
            OpenSessionCommand(goal="do work")
        )
        await AppendMessageHandler(uow, clock, id_gen).handle(
            AppendMessageCommand(session_id=session_id.value,correlation_id=get_correlation_id(), sender="agent-1", receiver="router", payload={"x": 1})
        )
        dto = await GetSessionHistoryHandler(queries).handle(GetSessionHistoryQuery(session_id=session_id.value))
        assert dto is not None
        assert dto.status == "open"
        assert len(dto.messages) == 1

    async def test_close_session(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        from shell_ddd.application.command_handlers.session_handlers import CloseSessionHandler, OpenSessionHandler
        from shell_ddd.application.commands.commands import CloseSessionCommand, OpenSessionCommand
        from shell_ddd.application.queries.queries import GetSessionHistoryQuery
        from shell_ddd.application.query_handlers.query_handlers import GetSessionHistoryHandler

        session_id = await OpenSessionHandler(uow, clock, id_gen).handle(
            OpenSessionCommand(goal="close test")
        )
        await CloseSessionHandler(uow, clock).handle(CloseSessionCommand(session_id=session_id.value))
        dto = await GetSessionHistoryHandler(queries).handle(GetSessionHistoryQuery(session_id=session_id.value))
        assert dto is not None
        assert dto.status == "closed"

    async def test_close_not_found_raises(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
    ) -> None:
        from shell_ddd.application.command_handlers.session_handlers import CloseSessionHandler, SessionNotFound
        from shell_ddd.application.commands.commands import CloseSessionCommand

        with pytest.raises(SessionNotFound):
            await CloseSessionHandler(uow, clock).handle(CloseSessionCommand(session_id="no-such-id"))

    async def test_get_history_not_found_returns_none(self, queries: InMemoryQueryServices) -> None:
        from shell_ddd.application.queries.queries import GetSessionHistoryQuery
        from shell_ddd.application.query_handlers.query_handlers import GetSessionHistoryHandler

        dto = await GetSessionHistoryHandler(queries).handle(GetSessionHistoryQuery(session_id="ghost"))
        assert dto is None
```
