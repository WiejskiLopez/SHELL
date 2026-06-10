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
from shell_ddd.domain.entities.template_graph import TemplateGraph
from shell_ddd.domain.entities.template_graph_node import TemplateGraphNode
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
    WorkflowId, CorrelationId, TemplateGraphId, TemplateGraphNodeId,
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
    workflow_model_to_entity, template_graph_entity_to_model, template_graph_model_to_entity,
    template_graph_node_model_to_entity, template_graph_node_entity_to_model,
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
    WorkflowModel, TemplateGraphModel, TemplateGraphNodeModel,
)

import logging

logger = logging.getLogger(__name__)


class SqlTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, task_id: TaskId) -> Task | None:
        q = (
            select(TaskModel)
            .options(selectinload(TaskModel.graph))
            .where(TaskModel.id == task_id.value)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return task_model_to_entity(row) if row else None

    async def get_by_name(self, name: TaskName) -> Task | None:
        q = (
            select(TaskModel)
            .options(selectinload(TaskModel.graph))
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
            .options(selectinload(TaskModel.graph))
            .where(TaskModel.name == name.value, TaskModel.is_current.is_(True))
            .limit(1)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if not row:
            logger.info("No current Task found for name=%s", name.value)
            return None

        logger.info(
            "TaskModel found: id=%s name=%s template_graph_id=%s is_current=%s",
            row.id,
            row.name,
            row.template_graph_id,
            row.is_current,
        )
        return task_model_to_entity(row) if row else None

    async def save(self, task: Task) -> None:
        model = task_entity_to_model(task)
        await self._session.merge(model)

    async def list_current(self) -> list[Task]:
        q = (
            select(TaskModel)
            .options(selectinload(TaskModel.graph))
            .where(TaskModel.is_current.is_(True))
        )
        rows = (await self._session.execute(q)).scalars().all()
        return [task_model_to_entity(r) for r in rows]


class SqlWorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        q = (
            select(WorkflowModel)
            .options(selectinload(WorkflowModel.node_states))
            .where(WorkflowModel.id == workflow_id.value)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return workflow_model_to_entity(row) if row else None

    async def save(self, workflow: Workflow) -> None:
        # Delete existing node_states to avoid conflicts, then merge
        await self._session.execute(
            update(WorkflowModel)
            .where(WorkflowModel.id == workflow.id.value)
            .values(status=workflow.status.value)
        )
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


class SqlNodeResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, result_id: NodeResultId) -> NodeResult | None:
        q = select(NodeResultModel).where(NodeResultModel.id == result_id.value)
        row = (await self._session.execute(q)).scalar_one_or_none()
        return node_result_model_to_entity(row) if row else None

    async def get_by_node_and_workflow(
            self, node_id: NodeId, workflow_id: WorkflowId
    ) -> NodeResult | None:
        q = select(NodeResultModel).where(
            NodeResultModel.node_id == node_id.value,
            NodeResultModel.workflow_id == workflow_id.value,
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return node_result_model_to_entity(row) if row else None

    async def save(self, result: NodeResult) -> None:
        model = node_result_entity_to_model(result)
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
