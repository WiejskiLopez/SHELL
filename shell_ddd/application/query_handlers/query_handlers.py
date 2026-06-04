"""Query handlers — read-side, return DTOs."""
from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from shell_ddd.application.mappers.mappers import (
    envelope_to_dto,
    node_result_to_dto,
    prompt_to_dto,
    runner_config_to_dto,
    task_to_dto,
    workflow_to_dto,
)
from shell_ddd.domain.services.rag_index_service import Embedder, _encode_vector, cosine_similarity
from shell_ddd.domain.value_objects.ids import NodeId, SessionId, WorkflowId
from shell_ddd.domain.value_objects.task_name import TaskName

if TYPE_CHECKING:
    from shell_ddd.application.dto.dto import (
        EnvelopeDto,
        MessageDto,
        NodeResultDto,
        PromptDto,
        RagChunkDto,
        RunnerConfigDto,
        SessionDto,
        TaskDto,
        WorkflowDto,
    )
    from shell_ddd.application.ports.ports import UnitOfWork
    from shell_ddd.application.queries.queries import (
        GetCurrentTaskQuery,
        GetEnvelopesByWorkflowQuery,
        GetNodeResultQuery,
        GetPromptQuery,
        GetRunnerConfigQuery,
        GetSessionHistoryQuery,
        GetTaskByNameQuery,
        GetWorkflowQuery,
        SearchSimilarQuery,
    )


class GetTaskByNameHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetTaskByNameQuery) -> TaskDto | None:
        async with self._uow as uow:
            task = await uow.tasks.get_by_name(TaskName(query.name))
            return task_to_dto(task) if task else None


class GetCurrentTaskHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetCurrentTaskQuery) -> TaskDto | None:
        async with self._uow as uow:
            task = await uow.tasks.get_current_by_name(TaskName(query.name))
            return task_to_dto(task) if task else None


class GetWorkflowHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetWorkflowQuery) -> WorkflowDto | None:
        async with self._uow as uow:
            wf = await uow.workflows.get_by_id(WorkflowId(query.workflow_id))
            return workflow_to_dto(wf) if wf else None


class GetEnvelopesByWorkflowHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetEnvelopesByWorkflowQuery) -> list[EnvelopeDto]:
        async with self._uow as uow:
            wf_id = WorkflowId(query.workflow_id)
            envelopes = (
                await uow.envelopes.list_pending(wf_id)
                if query.pending_only
                else await uow.envelopes.list_by_workflow(wf_id)
            )
            return [envelope_to_dto(e) for e in envelopes]


class GetNodeResultHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetNodeResultQuery) -> NodeResultDto | None:
        async with self._uow as uow:
            result = await uow.node_results.get_by_node_and_workflow(
                NodeId(query.node_id),
                WorkflowId(query.workflow_id),
            )
            return node_result_to_dto(result) if result else None


class GetPromptHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetPromptQuery) -> PromptDto | None:
        async with self._uow as uow:
            prompt = await uow.prompts.get_current_by_name(query.name)
            return prompt_to_dto(prompt) if prompt else None


class GetRunnerConfigHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetRunnerConfigQuery) -> RunnerConfigDto | None:
        async with self._uow as uow:
            config = await uow.runner_configs.get_by_package(query.package_name)
            return runner_config_to_dto(config) if config else None


class SearchSimilarHandler:
    def __init__(self, uow: UnitOfWork, embedder: Embedder) -> None:
        self._uow = uow
        self._embedder = embedder

    async def handle(self, query: SearchSimilarQuery) -> list[RagChunkDto]:
        from shell_ddd.application.dto.dto import RagChunkDto

        query_vec = self._embedder.embed_text(query.query_text)
        query_blob = _encode_vector(query_vec)
        async with self._uow as uow:
            chunks = await uow.rag_documents.search_similar(
                query_blob, top_k=query.top_k, domain=query.domain
            )
        results: list[RagChunkDto] = []
        for chunk in chunks:
            chunk_vec = list(
                struct.unpack(f"{len(chunk.embedding) // 4}f", chunk.embedding)
            )
            score = cosine_similarity(query_vec, chunk_vec)
            results.append(
                RagChunkDto(
                    chunk_id=chunk.id.value,
                    document_id=chunk.document_id.value,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    source_uri="",
                    title="",
                    domain=query.domain or "",
                    score=score,
                )
            )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[: query.top_k]


class GetSessionHistoryHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetSessionHistoryQuery) -> SessionDto | None:
        from shell_ddd.application.dto.dto import MessageDto, SessionDto

        async with self._uow as uow:
            session = await uow.sessions.get_by_id(SessionId(query.session_id))
            if session is None:
                return None
            messages = await uow.sessions.get_messages(session.id)
        return SessionDto(
            id=session.id.value,
            agent_id=session.agent_id,
            goal=session.goal,
            status=session.status,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
            messages=[
                MessageDto(
                    id=m.id.value,
                    session_id=m.session_id.value,
                    sender=m.sender,
                    receiver=m.receiver,
                    payload=m.payload,
                    created_at=m.created_at,
                )
                for m in messages
            ],
        )
