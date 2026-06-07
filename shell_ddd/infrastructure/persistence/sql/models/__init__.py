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
    template_graph_id: Mapped[str] = mapped_column(String(36), nullable=False, default="")
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
