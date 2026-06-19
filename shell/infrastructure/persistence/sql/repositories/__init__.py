"""SQL repository adapters (SQLite + PostgreSQL via SQLAlchemy 2.x async)."""

from __future__ import annotations

import logging
import struct
from typing import TYPE_CHECKING

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from shell.domain.entities.rag_document import RagChunk, RagDocument
from shell.domain.entities.session import Message, Session
from shell.domain.repositories.envelope_repository import EnvelopeArchive, EnvelopeRepository
from shell.domain.repositories.graph_definition_repository import GraphDefinitionRepository
from shell.domain.repositories.graph_execution_repository import GraphExecutionRepository
from shell.domain.repositories.prompt_repository import PromptRepository
from shell.domain.repositories.rag_repository import RagDocumentRepository
from shell.domain.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.repositories.session_repository import SessionRepository
from shell.domain.repositories.task_execution_repository import TaskExecutionRepository
from shell.domain.repositories.workflow_repository import WorkflowRepository
from shell.domain.services.rag_index_service import cosine_similarity
from shell.domain.value_objects.envelope_status import EnvelopeStatus
from shell.domain.value_objects.ids import (
    CorrelationId,
    EnvelopeId,
    GraphDefinitionId,
    GraphExecutionId,
    GraphNodeDefinitionId,
    GraphNodeExecutionId,
    MessageId,
    PromptId,
    RagChunkId,
    RagDocumentId,
    RunnerConfigId,
    SessionId,
    TaskExecutionId,
    WorkflowId,
)

__all__ = [
    "EnvelopeArchive",
    "EnvelopeRepository",
    "GraphExecutionRepository",
    "PromptRepository",
    "RagDocumentRepository",
    "RunnerConfigRepository",
    "SessionRepository",
    "TaskExecutionRepository",
    "GraphDefinitionRepository",
    "WorkflowRepository",
    "SqlTaskExecutionRepository",
    "SqlTaskExecutionInputPayloadRepository",
    "SqlTaskExecutionOutputPayloadRepository",
    "SqlGraphNodeExecutionInputPayloadRepository",
    "SqlGraphNodeExecutionOutputPayloadRepository",
    "SqlGraphExecutionRepository",
    "SqlWorkflowRepository",
    "SqlEnvelopeRepository",
    "SqlPromptRepository",
    "SqlRunnerConfigRepository",
    "SqlEnvelopeArchiveStub",
    "SqlRagDocumentRepository",
    "SqlSessionRepository",
    "SqlGraphDefinitionRepository",
    "SqlGraphNodeDefinitionRepository",
]

from shell.infrastructure.persistence.sql.mappers import (  # noqa: E501
    envelope_entity_to_model,
    envelope_model_to_entity,
    graph_definition_entity_to_model,
    graph_definition_model_to_entity,
    graph_execution_entity_to_model,
    graph_execution_model_to_entity,
    graph_node_definition_entity_to_model,
    graph_node_definition_model_to_entity,
    graph_node_execution_input_payload_entity_to_model,
    graph_node_execution_input_payload_model_to_entity,
    graph_node_execution_output_payload_entity_to_model,
    graph_node_execution_output_payload_model_to_entity,
    prompt_entity_to_model,
    prompt_model_to_entity,
    runner_config_entity_to_model,
    runner_config_model_to_entity,
    task_execution_entity_to_model,
    task_execution_input_payload_entity_to_model,
    task_execution_input_payload_model_to_entity,
    task_execution_model_to_entity,
    task_execution_output_payload_entity_to_model,
    task_execution_output_payload_model_to_entity,
    workflow_entity_to_model,
    workflow_model_to_entity,
)
from shell.infrastructure.persistence.sql.models import (
    EnvelopeModel,
    GraphDefinitionModel,
    GraphExecutionModel,
    GraphNodeDefinitionModel,
    GraphNodeExecutionInputPayloadModel,
    GraphNodeExecutionOutputPayloadModel,
    MessageModel,
    PromptModel,
    RagChunkModel,
    RagDocumentModel,
    RunnerConfigModel,
    SessionModel,
    TaskExecutionInputPayloadModel,
    TaskExecutionModel,
    TaskExecutionOutputPayloadModel,
    WorkflowModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.entities.envelope import Envelope
    from shell.domain.entities.graph_definition import GraphDefinition
    from shell.domain.aggregates.graph_execution import GraphExecution
    from shell.domain.entities.graph_node_definition import GraphNodeDefinition
    from shell.domain.entities.prompt import Prompt
    from shell.domain.entities.runner_config import RunnerConfig
    from shell.domain.aggregates.task_execution import TaskExecution
    from shell.domain.aggregates.graph_node_execution_input_payload import (
        GraphNodeExecutionInputPayload,
    )
    from shell.domain.aggregates.graph_node_execution_output_payload import (
        GraphNodeExecutionOutputPayload,
    )
    from shell.domain.aggregates.task_execution_input_payload import (
        TaskExecutionInputPayload,
    )
    from shell.domain.aggregates.task_execution_output_payload import (
        TaskExecutionOutputPayload,
    )
    from shell.domain.aggregates.workflow import Workflow
    from shell.domain.value_objects.task_execution_name import TaskExecutionName

logger = logging.getLogger(__name__)


class SqlTaskExecutionRepository(TaskExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, task_execution_id: TaskExecutionId) -> TaskExecution | None:
        query = select(TaskExecutionModel).where(TaskExecutionModel.id == task_execution_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_model_to_entity(row) if row else None

    async def get_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        query = (
            select(TaskExecutionModel)
            .where(TaskExecutionModel.name == name.value)
            .order_by(TaskExecutionModel.version.desc())
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_model_to_entity(row) if row else None

    async def get_current_by_id(self, id: TaskExecutionId) -> TaskExecution | None:
        logger.info("Querying current Task by id=%s", id.value)
        query = (
            select(TaskExecutionModel)
            .where(
                TaskExecutionModel.id == task_execution_id.value,
                TaskExecutionModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        if not row:
            logger.info("No current Task found for id=%s", id.value)
            return None

        logger.info(
            "TaskExecutionModel found: id=%s name=%s is_current=%s",
            row.id,
            row.name,
            row.is_current,
        )
        return task_execution_model_to_entity(row)

    async def get_current_by_name(self, name: TaskExecutionName) -> TaskExecution | None:
        logger.info("Querying current Task by name=%s", name.value)
        query = (
            select(TaskExecutionModel)
            .where(TaskExecutionModel.name == name.value, TaskExecutionModel.is_current.is_(True))
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        if not row:
            logger.info("No current Task found for name=%s", name.value)
            return None

        logger.info(
            "TaskExecutionModel found: id=%s name=%s is_current=%s",
            row.id,
            row.name,
            row.is_current,
        )
        return task_execution_model_to_entity(row)

    async def save(self, task_execution: TaskExecution) -> None:
        model = task_execution_entity_to_model(task_execution)
        await self._session.merge(model)

    async def list_current(self) -> list[TaskExecution]:
        query = select(TaskExecutionModel).where(TaskExecutionModel.is_current.is_(True))
        rows = (await self._session.execute(query)).scalars().all()
        return [task_execution_model_to_entity(row) for row in rows]


class SqlTaskExecutionInputPayloadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionInputPayload | None:
        query = (
            select(TaskExecutionInputPayloadModel)
            .where(
                TaskExecutionInputPayloadModel.task_execution_id == task_execution_id.value,
                TaskExecutionInputPayloadModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_input_payload_model_to_entity(row) if row else None

    async def save(self, payload: TaskExecutionInputPayload) -> None:
        model = task_execution_input_payload_entity_to_model(payload)
        await self._session.merge(model)


class SqlTaskExecutionOutputPayloadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionOutputPayload | None:
        query = (
            select(TaskExecutionOutputPayloadModel)
            .where(
                TaskExecutionOutputPayloadModel.task_execution_id == task_execution_id.value,
                TaskExecutionOutputPayloadModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return task_execution_output_payload_model_to_entity(row) if row else None

    async def save(self, payload: TaskExecutionOutputPayload) -> None:
        model = task_execution_output_payload_entity_to_model(payload)
        await self._session.merge(model)


class SqlGraphNodeExecutionInputPayloadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionInputPayload | None:
        query = (
            select(GraphNodeExecutionInputPayloadModel)
            .where(
                GraphNodeExecutionInputPayloadModel.graph_node_execution_id == graph_node_execution_id.value,
                GraphNodeExecutionInputPayloadModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_node_execution_input_payload_model_to_entity(row) if row else None

    async def save(self, payload: GraphNodeExecutionInputPayload) -> None:
        model = graph_node_execution_input_payload_entity_to_model(payload)
        await self._session.merge(model)


class SqlGraphNodeExecutionOutputPayloadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionOutputPayload | None:
        query = (
            select(GraphNodeExecutionOutputPayloadModel)
            .where(
                GraphNodeExecutionOutputPayloadModel.graph_node_execution_id == graph_node_execution_id.value,
                GraphNodeExecutionOutputPayloadModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_node_execution_output_payload_model_to_entity(row) if row else None

    async def save(self, payload: GraphNodeExecutionOutputPayload) -> None:
        model = graph_node_execution_output_payload_entity_to_model(payload)
        await self._session.merge(model)


class SqlGraphExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, graph_execution_id: GraphExecutionId) -> GraphExecution | None:
        query = (
            select(GraphExecutionModel)
            .options(selectinload(GraphExecutionModel.graph_node_execution_models))
            .where(GraphExecutionModel.id == graph_execution_id.value)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_execution_model_to_entity(row) if row else None

    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> GraphExecution | None:
        query = (
            select(GraphExecutionModel)
            .options(selectinload(GraphExecutionModel.graph_node_execution_models))
            .where(GraphExecutionModel.task_execution_id == task_execution_id.value)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_execution_model_to_entity(row) if row else None

    async def save(self, graph_execution: GraphExecution) -> None:
        graph_execution_model = graph_execution_entity_to_model(graph_execution)
        await self._session.merge(graph_execution_model)


class SqlWorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        query = (
            select(WorkflowModel)
            .options(
                selectinload(WorkflowModel.graph_node_execution_state_models),
                selectinload(WorkflowModel.graph_node_execution_result_models),
            )
            .where(WorkflowModel.id == workflow_id.value)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return workflow_model_to_entity(row) if row else None

    async def save(self, workflow: Workflow) -> None:
        """Persist the workflow with optimistic concurrency control (CAS).

        On first save (no row exists yet) the aggregate's ``version`` is
        bumped from 0 to 1 and the row is inserted via merge. On subsequeryuent
        saves a CAS UPDATE asserts that the persisted ``version`` still
        equeryuals the aggregate's loaded version; on success the persisted
        version is bumped to ``version + 1`` and mirrored on the aggregate.
        On mismatch :class:`WorkflowConcurrentlyModified` is raised.
        """
        from shell.domain.exceptions import WorkflowConcurrentlyModified

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

        # Subsequeryuent save — CAS on persisted version.
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
                current_graph_node_execution_id=(
                    workflow.cursor.current_graph_node_execution_id.value
                    if workflow.cursor.current_graph_node_execution_id
                    else None
                ),
                work_dir=workflow.execution_context.work_dir,
                correlation_id=workflow.execution_context.correlation_id,
                version=new_version,
            )
        )
        result = await self._session.execute(cas_stmt)
        if (result.rowcount if hasattr(result, "rowcount") else 0) == 0:
            raise WorkflowConcurrentlyModified(workflow.id.value)

        workflow.version = new_version
        model = workflow_entity_to_model(workflow)
        await self._session.merge(model)


class SqlEnvelopeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None:
        query = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(EnvelopeModel.id == envelope_id.value)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return envelope_model_to_entity(row) if row else None

    async def save(self, envelope: Envelope) -> None:
        model = envelope_entity_to_model(envelope)
        await self._session.merge(model)

    async def list_by_workflow(
        self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0
    ) -> list[Envelope]:
        query = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(EnvelopeModel.workflow_id == workflow_id.value)
            .offset(offset)
        )
        if limit is not None:
            query = query.limit(limit)
        rows = (await self._session.execute(query)).scalars().all()
        return [envelope_model_to_entity(row) for row in rows]

    async def list_pending(
        self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0
    ) -> list[Envelope]:
        query = (
            select(EnvelopeModel)
            .options(selectinload(EnvelopeModel.events))
            .where(
                EnvelopeModel.workflow_id == workflow_id.value,
                EnvelopeModel.status == EnvelopeStatus.PENDING.value,
            )
            .offset(offset)
        )
        if limit is not None:
            query = query.limit(limit)
        rows = (await self._session.execute(query)).scalars().all()
        return [envelope_model_to_entity(row) for row in rows]


class SqlPromptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, prompt_id: PromptId) -> Prompt | None:
        query = select(PromptModel).where(PromptModel.id == prompt_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return prompt_model_to_entity(row) if row else None

    async def get_current_by_name(self, name: str) -> Prompt | None:
        query = select(PromptModel).where(PromptModel.name == name, PromptModel.is_current.is_(True))
        row = (await self._session.execute(query)).scalar_one_or_none()
        return prompt_model_to_entity(row) if row else None

    async def save(self, prompt: Prompt) -> None:
        model = prompt_entity_to_model(prompt)
        await self._session.merge(model)


class SqlRunnerConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None:
        query = select(RunnerConfigModel).where(RunnerConfigModel.id == config_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return runner_config_model_to_entity(row) if row else None

    async def get_by_package(self, package_name: str) -> RunnerConfig | None:
        query = select(RunnerConfigModel).where(RunnerConfigModel.package_name == package_name)
        row = (await self._session.execute(query)).scalar_one_or_none()
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
        query = (
            select(RagDocumentModel)
            .options(selectinload(RagDocumentModel.chunks))
            .where(RagDocumentModel.id == doc_id.value)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        if row is None:
            return None
        doc = RagDocument(
            id=RagDocumentId(row.id),
            source_uri=row.source_uri,
            title=row.title,
            domain=row.domain,
            created_at=row.created_at,
        )
        for chunk in sorted(row.chunks, key=lambda chunk_entry: chunk_entry.chunk_index):
            doc.chunks.append(
                RagChunk(
                    id=RagChunkId(chunk.id),
                    document_id=RagDocumentId(chunk.document_id),
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    embedding=chunk.embedding,
                    embedding_model=chunk.embedding_model,
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
        query = select(RagChunkModel).options(selectinload(RagChunkModel.document))
        if domain:
            query = query.join(RagDocumentModel).where(RagDocumentModel.domain == domain)
        rows = (await self._session.execute(query)).scalars().all()
        if not rows:
            return []
        dim = len(query_embedding) // 4
        query_vec = list(struct.unpack(f"{dim}f", query_embedding))
        scored: list[tuple[float, RagChunkModel]] = []
        for rag_chunk_model in rows:
            chunk_vec = list(struct.unpack(f"{len(rag_chunk_model.embedding) // 4}f", rag_chunk_model.embedding))
            score = cosine_similarity(query_vec, chunk_vec)
            scored.append((score, rag_chunk_model))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [
            RagChunk(
                id=RagChunkId(rag_chunk_model.id),
                document_id=RagDocumentId(rag_chunk_model.document_id),
                chunk_index=rag_chunk_model.chunk_index,
                chunk_text=rag_chunk_model.chunk_text,
                embedding=rag_chunk_model.embedding,
                embedding_model=rag_chunk_model.embedding_model,
            )
            for _, rag_chunk_model in scored[:top_k]
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
        query = select(SessionModel).where(SessionModel.id == session_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
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
        query = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id.value)
            .order_by(MessageModel.created_at)
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [
            Message(
                id=MessageId(message_model.id),
                session_id=SessionId(message_model.session_id),
                correlation_id=CorrelationId(message_model.correlation_id),
                sender=message_model.sender,
                receiver=message_model.receiver,
                payload=message_model.payload,
                created_at=message_model.created_at,
            )
            for message_model in rows
        ]


class SqlGraphDefinitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, graph_definition_id: GraphDefinitionId) -> GraphDefinition | None:
        query = select(GraphDefinitionModel).where(GraphDefinitionModel.id == graph_definition_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_definition_model_to_entity(row) if row else None

    async def get_graph_definition_by_name(
        self, graph_definition_by_name: str
    ) -> GraphDefinition | None:
        query = (
            select(GraphDefinitionModel)
            .options(selectinload(GraphDefinitionModel.graph_node_execution_models))
            .where(GraphDefinitionModel.name == graph_definition_by_name)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_definition_model_to_entity(row) if row else None

    async def save(self, graph_definition: GraphDefinition) -> None:
        graph_definition_model = graph_definition_entity_to_model(graph_definition)
        await self._session.merge(graph_definition_model)


class SqlGraphNodeDefinitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, graph_node_definition_execution_id: GraphNodeDefinitionId
    ) -> GraphNodeDefinition | None:
        graph_node_definition_query = select(GraphNodeDefinitionModel).where(
            GraphNodeDefinitionModel.id == graph_node_definition_execution_id.value
        )
        graph_node_definition = (
            await self._session.execute(graph_node_definition_query)
        ).scalar_one_or_none()
        return (
            graph_node_definition_model_to_entity(graph_node_definition)
            if graph_node_definition
            else None
        )

    async def save(
        self, graph_node_definition: GraphNodeDefinition, graph_definition_id: GraphDefinitionId
    ) -> None:
        graph_definition = await self._session.get(GraphDefinitionModel, graph_definition_id.value)
        if not graph_definition:
            raise ValueError(f"GraphDefinition {graph_definition_id.value} not found")

        graph_node_definition_model = graph_node_definition_entity_to_model(
            graph_node_definition, graph_definition_id.value
        )
        await self._session.merge(graph_node_definition_model)
