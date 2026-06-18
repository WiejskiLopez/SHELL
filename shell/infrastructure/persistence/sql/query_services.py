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
                        id=graph_node_execution_model.id,
                        position=graph_node_execution_model.position,
                        node_dir=graph_node_execution_model.node_dir,
                        mode=graph_node_execution_model.mode,
                        role=graph_node_execution_model.role,
                        node_type=graph_node_execution_model.node_type,
                        model=graph_node_execution_model.model,
                        command=graph_node_execution_model.command,
                    )
                    for graph_node_execution_model in graph_model.graph_node_execution_models
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
                    state_model.graph_node_execution_id: GraphNodeExecutionStateDto(
                        graph_node_execution_id=state_model.graph_node_execution_id,
                        status=state_model.status,
                        step=state_model.step,
                        updated_at=state_model.updated_at,
                    )
                    for state_model in model.graph_node_execution_state_models
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
                    id=envelope_model.id,
                    workflow_id=envelope_model.workflow_id,
                    sender_graph_node_execution_id=envelope_model.sender_graph_node_execution_id,
                    receiver_graph_node_execution_id=envelope_model.receiver_graph_node_execution_id,
                    source_role=envelope_model.source_role,
                    target_role=envelope_model.target_role,
                    status=envelope_model.status,
                    stage=envelope_model.stage,
                    step=envelope_model.step,
                    payload=envelope_model.payload,
                    created_at=envelope_model.created_at,
                    updated_at=envelope_model.updated_at,
                )
                for envelope_model in res.scalars()
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
            result_model = next(
                (
                    node_result_model
                    for node_result_model in wf.graph_node_execution_result_models
                    if node_result_model.graph_node_execution_id == graph_node_execution_id
                ),
                None,
            )
            if not result_model:
                return None
            return GraphNodeExecutionResultDto(
                id=result_model.id,
                graph_node_execution_id=result_model.graph_node_execution_id,
                workflow_id=result_model.workflow_id,
                status=result_model.status,
                stdout=result_model.stdout,
                stderr=result_model.stderr,
                artifact_uri=result_model.artifact_uri,
                created_at=result_model.created_at,
            )

    # --- PromptQueryService ---
    async def get_prompt(self, name: str) -> PromptDto | None:
        async with self._session_factory() as session:
            stmt = select(PromptModel).where(PromptModel.name == name)
            res = await session.execute(stmt)
            prompt_model = res.scalar_one_or_none()
            if not prompt_model:
                return None
            return PromptDto(
                id=prompt_model.id,
                name=prompt_model.name,
                body=prompt_model.body,
                version=prompt_model.version,
                hash=prompt_model.hash,
                is_current=prompt_model.is_current,
                created_at=prompt_model.created_at,
            )

    # --- RunnerConfigQueryService ---
    async def get_runner_config(self, package_name: str) -> RunnerConfigDto | None:
        async with self._session_factory() as session:
            stmt = select(RunnerConfigModel).where(RunnerConfigModel.package_name == package_name)
            res = await session.execute(stmt)
            runner_config_model = res.scalar_one_or_none()
            if not runner_config_model:
                return None
            return RunnerConfigDto(
                id=runner_config_model.id,
                package_name=runner_config_model.package_name,
                kind=runner_config_model.kind,
                hash=runner_config_model.hash,
                body=runner_config_model.body,
                created_at=runner_config_model.created_at,
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
                    chunk_id=str(rag_chunk_model.id),
                    document_id=str(rag_chunk_model.document_id),
                    chunk_index=rag_chunk_model.chunk_index,
                    chunk_text=rag_chunk_model.chunk_text,
                    source_uri=rag_chunk_model.document.source_uri,
                    title=rag_chunk_model.document.title,
                    domain=rag_chunk_model.document.domain,
                    score=0.0,
                )
                for rag_chunk_model in res.scalars()
            ][:top_k]
