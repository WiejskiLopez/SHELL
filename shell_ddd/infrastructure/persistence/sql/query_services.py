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