"""Implementacje portów odczytu przy użyciu SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from shell.application.dto.dto import (
    EnvelopeDto,
    GraphNodeExecutionDto,
    GraphNodeExecutionResultDto,
    GraphNodeExecutionStateDto,
    MessageDto,
    PromptDto,
    RagChunkDto,
    RunnerConfigDto,
    SessionDto,
    TaskExecutionDto,
    WorkflowDto,
)
from shell.infrastructure.persistence.sql.models import (
    EnvelopeModel,
    GraphExecutionModel,
    PromptModel,
    RagChunkModel,
    RagDocumentModel,
    RunnerConfigModel,
    SessionModel,
    TaskExecutionModel,
    WorkflowModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SqlQueryServices:
    """Zbiorcza klasa implementująca wszystkie interfejsy QueryService (Read Model)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    # --- TaskExecutionQueryService ---
    async def get_task_execution_by_name(self, name: str) -> TaskExecutionDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(TaskExecutionModel)
                .where(TaskExecutionModel.name == name)
                .where(TaskExecutionModel.is_current)
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None

            graph_stmt = (
                select(GraphExecutionModel)
                .options(selectinload(GraphExecutionModel.graph_node_execution_models))
                .where(GraphExecutionModel.task_execution_id == model.id)
            )
            graph_res = await session.execute(graph_stmt)
            graph_model = graph_res.scalar_one_or_none()

            graph_node_executions: list[GraphNodeExecutionDto] = []
            if graph_model is not None:
                graph_node_executions = [
                    GraphNodeExecutionDto(
                        id=n.id,
                        position=n.position,
                        node_dir=n.node_dir,
                        mode=n.mode,
                        role=n.role,
                        node_type=n.node_type,
                        model=n.model,
                        command=n.command,
                    )
                    for n in graph_model.graph_node_execution_models
                ]

            return TaskExecutionDto(
                id=model.id,
                name=model.name,
                version=model.version,
                hash=model.hash,
                is_current=model.is_current,
                created_at=model.created_at,
                body=model.body,
                graph_node_executions=graph_node_executions,
            )

    async def get_current_task(self, name: str) -> TaskExecutionDto | None:
        # W tej implementacji current_task jest tożsamy z pobraniem po nazwie
        return await self.get_task_execution_by_name(name)

    # --- WorkflowQueryService ---
    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(WorkflowModel)
                .options(selectinload(WorkflowModel.graph_node_execution_state_models))
                .where(WorkflowModel.id == workflow_id)
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return WorkflowDto(
                id=model.id,
                task_execution_id=model.task_execution_id,
                status=model.status,
                created_at=model.created_at,
                graph_node_execution_states={
                    n.graph_node_execution_id: GraphNodeExecutionStateDto(
                        graph_node_execution_id=n.graph_node_execution_id,
                        status=n.status,
                        step=n.step,
                        updated_at=n.updated_at,
                    )
                    for n in model.graph_node_execution_state_models
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
                    sender_graph_node_execution_id=m.sender_graph_node_execution_id,
                    receiver_graph_node_execution_id=m.receiver_graph_node_execution_id,
                    source_role=m.source_role,
                    target_role=m.target_role,
                    status=m.status,
                    stage=m.stage,
                    step=m.step,
                    payload=m.payload,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                )
                for m in res.scalars()
            ]

    # --- NodeResultQueryService ---
    async def get_graph_node_execution_result(
        self, graph_node_execution_id: str, workflow_id: str
    ) -> GraphNodeExecutionResultDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(WorkflowModel)
                .options(selectinload(WorkflowModel.graph_node_execution_result_models))
                .where(WorkflowModel.id == workflow_id)
            )
            res = await session.execute(stmt)
            wf = res.scalar_one_or_none()
            if not wf:
                return None
            m = next(
                (
                    nr
                    for nr in wf.graph_node_execution_result_models
                    if nr.graph_node_execution_id == graph_node_execution_id
                ),
                None,
            )
            if not m:
                return None
            return GraphNodeExecutionResultDto(
                id=m.id,
                graph_node_execution_id=m.graph_node_execution_id,
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
                created_at=m.created_at,
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
                id=m.id,
                package_name=m.package_name,
                kind=m.kind,
                hash=m.hash,
                body=m.body,
                created_at=m.created_at,
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
            session_model = res.scalar_one_or_none()
            if not session_model:
                return None
            return SessionDto(
                id=session_model.id,
                goal=session_model.goal,
                status=session_model.status,
                opened_at=session_model.opened_at,
                closed_at=session_model.closed_at,
                messages=[
                    MessageDto(
                        id=message.id,
                        session_id=message.session_id,
                        correlation_id=message.correlation_id,
                        sender=message.sender,
                        receiver=message.receiver,
                        payload=message.payload,
                        created_at=message.created_at,
                    )
                    for message in session_model.messages
                ],
            )

    # --- RagQueryService ---
    async def search_similar(
        self, query_embedding: bytes, top_k: int = 5, domain: str | None = None
    ) -> list[RagChunkDto]:
        async with self._session_factory() as session:
            stmt = select(RagChunkModel).options(joinedload(RagChunkModel.document))
            if domain:
                stmt = stmt.join(RagChunkModel.document).where(RagDocumentModel.domain == domain)
            res = await session.execute(stmt.limit(100))  # Przykładowy limit
            return [
                RagChunkDto(
                    chunk_id=str(c.id),
                    document_id=str(c.document_id),
                    chunk_index=c.chunk_index,
                    chunk_text=c.chunk_text,  # Zmieniono z 'content' na 'chunk_text'
                    source_uri=c.document.source_uri,  # Dane pobrane przez relację z RagDocumentModel
                    title=c.document.title,
                    domain=c.document.domain,
                    score=0.0,  # Tu docelowo wynik z wyszukiwania wektorowego
                )
                for c in res.scalars()
            ][:top_k]
