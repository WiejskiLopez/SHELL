"""SQLAlchemy 2.x ORM models — shared between SQLite and PostgreSQL."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TaskExecutionModel(Base):
    __tablename__ = "task_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, index=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    hash: Mapped[str] = mapped_column(nullable=False)
    body: Mapped[str] = mapped_column(nullable=False, default="")
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class TaskExecutionInputPayloadModel(Base):
    __tablename__ = "task_execution_input_payload"

    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(
        ForeignKey("task_execution.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class TaskExecutionOutputPayloadModel(Base):
    __tablename__ = "task_execution_output_payload"

    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(
        ForeignKey("task_execution.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class GraphNodeExecutionInputPayloadModel(Base):
    __tablename__ = "graph_node_execution_input_payload"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_node_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_node_execution.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class GraphNodeExecutionOutputPayloadModel(Base):
    __tablename__ = "graph_node_execution_output_payload"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_node_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_node_execution.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class GraphExecutionModel(Base):
    __tablename__ = "graph"

    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(
        ForeignKey("task_execution.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    graph_definition_id: Mapped[str] = mapped_column(nullable=False, default="")

    graph_node_execution_models: Mapped[list[GraphNodeExecutionModel]] = relationship(
        "GraphNodeExecutionModel",
        back_populates="graph_execution_model",
        cascade="all, delete-orphan",
    )


class GraphNodeExecutionModel(Base):
    __tablename__ = "graph_node_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(nullable=False, default=0)
    node_dir: Mapped[str] = mapped_column(nullable=False, default="")
    mode: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False, default="")
    node_type: Mapped[str] = mapped_column(nullable=False, default="")
    model: Mapped[str] = mapped_column(nullable=False, default="")
    command: Mapped[str] = mapped_column(nullable=False, default="")
    timeout: Mapped[int] = mapped_column(nullable=False, default=0)
    retries: Mapped[int] = mapped_column(nullable=False, default=0)
    log_level: Mapped[str] = mapped_column(nullable=False, default="INFO")
    max_step: Mapped[int] = mapped_column(nullable=False, default=0)
    no_ask_user: Mapped[bool] = mapped_column(nullable=False, default=False)
    autopilot: Mapped[bool] = mapped_column(nullable=False, default=False)
    task_execution_id: Mapped[str] = mapped_column(nullable=False, default="")
    source_dir: Mapped[str] = mapped_column(nullable=False, default="")
    work_dir: Mapped[str] = mapped_column(nullable=False, default="")
    status_initial: Mapped[str] = mapped_column(nullable=False, default="")
    extra: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]

    graph_execution_model: Mapped[GraphExecutionModel] = relationship(
        "GraphExecutionModel", back_populates="graph_node_execution_models"
    )


class WorkflowModel(Base):
    __tablename__ = "workflow"

    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(nullable=False, default="idle")
    current_graph_node_execution_id: Mapped[str | None] = mapped_column(
        nullable=True, default=None, index=True
    )
    work_dir: Mapped[str] = mapped_column(nullable=False, default="")
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    version: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    graph_node_execution_state_models: Mapped[list[GraphNodeExecutionStateModel]] = relationship(
        "GraphNodeExecutionStateModel",
        back_populates="workflow_model",
        cascade="all, delete-orphan",
    )

    graph_node_execution_result_models: Mapped[list[GraphNodeExecutionResultModel]] = relationship(
        "GraphNodeExecutionResultModel",
        primaryjoin="WorkflowModel.id == foreign(GraphNodeExecutionResultModel.workflow_id)",
        cascade="all, delete-orphan",
    )


class GraphNodeExecutionStateModel(Base):
    __tablename__ = "node_state"

    id: Mapped[str] = mapped_column(primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        ForeignKey("workflow.id", ondelete="CASCADE"), nullable=False, index=True
    )
    graph_node_execution_id: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="idle")
    step: Mapped[int] = mapped_column(nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    workflow_model: Mapped[WorkflowModel] = relationship(
        "WorkflowModel", back_populates="graph_node_execution_state_models"
    )


class EnvelopeModel(Base):
    __tablename__ = "envelope"

    id: Mapped[str] = mapped_column(primary_key=True)
    workflow_id: Mapped[str] = mapped_column(nullable=False, index=True)
    parent_id: Mapped[str | None] = mapped_column(nullable=True)
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    sender_graph_node_execution_id: Mapped[str] = mapped_column(nullable=False)
    receiver_graph_node_execution_id: Mapped[str] = mapped_column(nullable=False)
    source_role: Mapped[str] = mapped_column(nullable=False, default="")
    target_role: Mapped[str] = mapped_column(nullable=False, default="")
    sequence_id: Mapped[int] = mapped_column(nullable=False, default=0)
    step: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(nullable=False, default="pending")
    stage: Mapped[str] = mapped_column(nullable=False, default="draft")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    artifact_uri: Mapped[str] = mapped_column(nullable=False, default="")
    archive_uri: Mapped[str] = mapped_column(nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    events: Mapped[list[EnvelopeEventModel]] = relationship(
        "EnvelopeEventModel", back_populates="envelope", cascade="all, delete-orphan"
    )


class EnvelopeEventModel(Base):
    __tablename__ = "envelope_event"

    id: Mapped[str] = mapped_column(primary_key=True)
    envelope_id: Mapped[str] = mapped_column(
        ForeignKey("envelope.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    envelope: Mapped[EnvelopeModel] = relationship("EnvelopeModel", back_populates="events")


class PromptModel(Base):
    __tablename__ = "prompt"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, index=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    hash: Mapped[str] = mapped_column(nullable=False)
    body: Mapped[str] = mapped_column(nullable=False, default="")
    source_uri: Mapped[str] = mapped_column(nullable=False, default="")
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class GraphNodeExecutionResultModel(Base):
    __tablename__ = "graph_node_execution_result"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_node_execution_id: Mapped[str] = mapped_column( nullable=False, index=True)
    workflow_id: Mapped[str] = mapped_column( nullable=False, index=True)
    status: Mapped[str] = mapped_column( nullable=False)
    stdout: Mapped[str] = mapped_column(nullable=False, default="")
    stderr: Mapped[str] = mapped_column(nullable=False, default="")
    artifact_uri: Mapped[str] = mapped_column(nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class RunnerConfigModel(Base):
    __tablename__ = "runner_config"

    id: Mapped[str] = mapped_column( primary_key=True)
    package_name: Mapped[str] = mapped_column( nullable=False, index=True)
    kind: Mapped[str] = mapped_column( nullable=False)
    hash: Mapped[str] = mapped_column( nullable=False)
    body: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class RagDocumentModel(Base):
    __tablename__ = "rag_document"

    id: Mapped[str] = mapped_column( primary_key=True)
    source_uri: Mapped[str] = mapped_column( nullable=False, index=True)
    title: Mapped[str] = mapped_column( nullable=False)
    domain: Mapped[str] = mapped_column( nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    chunks: Mapped[list[RagChunkModel]] = relationship(
        "RagChunkModel", back_populates="document", cascade="all, delete-orphan"
    )


class RagChunkModel(Base):
    __tablename__ = "rag_chunk"

    id: Mapped[str] = mapped_column( primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("rag_document.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(nullable=False, default=0)
    chunk_text: Mapped[str] = mapped_column(nullable=False)
    embedding: Mapped[bytes] = mapped_column(nullable=False)
    embedding_model: Mapped[str] = mapped_column( nullable=False)

    document: Mapped[RagDocumentModel] = relationship("RagDocumentModel", back_populates="chunks")


class SessionModel(Base):
    __tablename__ = "session"

    id: Mapped[str] = mapped_column( primary_key=True)
    goal: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="open")
    opened_at: Mapped[datetime] = mapped_column(nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    messages: Mapped[list[MessageModel]] = relationship(
        "MessageModel", back_populates="session", cascade="all, delete-orphan"
    )


class MessageModel(Base):
    __tablename__ = "message"

    id: Mapped[str] = mapped_column( primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )
    correlation_id: Mapped[str] = mapped_column( nullable=False, default="")
    sender: Mapped[str] = mapped_column( nullable=False)
    receiver: Mapped[str] = mapped_column( nullable=False)
    payload: Mapped[dict] = mapped_column("payload_json", JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="messages")


class AuditEventModel(Base):
    __tablename__ = "audit_event"

    id: Mapped[str] = mapped_column( primary_key=True)
    event_type: Mapped[str] = mapped_column( nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False, index=True
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]


class OutboxEventModel(Base):
    __tablename__ = "outbox_event"

    id: Mapped[str] = mapped_column( primary_key=True)
    event_type: Mapped[str] = mapped_column( nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)


class InboxEventModel(Base):
    __tablename__ = "inbox_event"

    id: Mapped[str] = mapped_column( primary_key=True)
    event_type: Mapped[str] = mapped_column( nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # type: ignore[type-arg]
    received_at: Mapped[datetime] = mapped_column(nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True, index=True
    )


class GraphDefinitionModel(Base):
    __tablename__ = "graph_definition"

    id: Mapped[str] = mapped_column( primary_key=True)
    name: Mapped[str] = mapped_column( nullable=False)
    purpose: Mapped[str] = mapped_column( nullable=False)

    graph_node_execution_models: Mapped[list[GraphNodeDefinitionModel]] = relationship(
        "GraphNodeDefinitionModel",
        back_populates="graph_definition_model",
        cascade="all, delete-orphan",
        order_by="GraphNodeDefinitionModel.position",
    )


class GraphNodeDefinitionModel(Base):
    __tablename__ = "graph_node_definition"

    id: Mapped[str] = mapped_column( primary_key=True)
    graph_definition_id: Mapped[str] = mapped_column(
        ForeignKey("graph_definition.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(nullable=False)
    mode: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column( nullable=False)
    node_type: Mapped[str] = mapped_column( nullable=False)
    model: Mapped[str | None] = mapped_column( nullable=True)
    command: Mapped[str] = mapped_column(nullable=False)
    timeout: Mapped[int] = mapped_column(nullable=False)
    retries: Mapped[int] = mapped_column(nullable=False)
    log_level: Mapped[str] = mapped_column(nullable=False)
    max_step: Mapped[int | None] = mapped_column(nullable=True)
    no_ask_user: Mapped[bool | None] = mapped_column(
        nullable=True,
    )
    autopilot: Mapped[bool | None] = mapped_column(
        nullable=True,
    )
    status_initial: Mapped[str] = mapped_column(
        nullable=False,
    )
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    script: Mapped[str | None] = mapped_column(
        nullable=True,
    )
    script_type: Mapped[str | None] = mapped_column(
        nullable=True,
    )

    graph_definition_model: Mapped[GraphDefinitionModel] = relationship(
        "GraphDefinitionModel",
        back_populates="graph_node_execution_models",
    )
