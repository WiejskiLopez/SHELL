"""Czyste handlery zapytań (CQRS) — omijają domenę i używają serwisów odczytu."""
from __future__ import annotations
from typing import TYPE_CHECKING

from shell_ddd.domain.services.rag_index_service import Embedder

if TYPE_CHECKING:
    from shell_ddd.application.dto.dto import (
        EnvelopeDto,
        NodeResultDto,
        PromptDto,
        RagChunkDto,
        RunnerConfigDto,
        SessionDto,
        TaskDto,
        WorkflowDto,
    )
    from shell_ddd.application.ports.queries import (
        EnvelopeQueryService,
        NodeResultQueryService,
        PromptQueryService,
        RagQueryService,
        RunnerConfigQueryService,
        SessionQueryService,
        TaskQueryService,
        WorkflowQueryService,
    )
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
    def __init__(self, queries: TaskQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetTaskByNameQuery) -> TaskDto | None:
        return await self._queries.get_task_by_name(query.name)


class GetCurrentTaskHandler:
    def __init__(self, queries: TaskQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetCurrentTaskQuery) -> TaskDto | None:
        return await self._queries.get_current_task(query.name)


class GetWorkflowHandler:
    def __init__(self, queries: WorkflowQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetWorkflowQuery) -> WorkflowDto | None:
        return await self._queries.get_workflow(query.workflow_id)


class GetEnvelopesByWorkflowHandler:
    def __init__(self, queries: EnvelopeQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetEnvelopesByWorkflowQuery) -> list[EnvelopeDto]:
        return await self._queries.get_envelopes_by_workflow(
            query.workflow_id, query.pending_only
        )


class GetNodeResultHandler:
    def __init__(self, queries: NodeResultQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetNodeResultQuery) -> NodeResultDto | None:
        return await self._queries.get_node_result(query.node_id, query.workflow_id)


class GetPromptHandler:
    def __init__(self, queries: PromptQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetPromptQuery) -> PromptDto | None:
        return await self._queries.get_prompt(query.name)


class GetRunnerConfigHandler:
    def __init__(self, queries: RunnerConfigQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetRunnerConfigQuery) -> RunnerConfigDto | None:
        return await self._queries.get_runner_config(query.package_name)


class SearchSimilarHandler:
    def __init__(self, queries: RagQueryService, embedder: Embedder) -> None:
        self._queries = queries
        self._embedder = embedder

    async def handle(self, query: SearchSimilarQuery) -> list[RagChunkDto]:
        vector = self._embedder.embed_text(query.query_text)
        return await self._queries.search_similar(vector, query.top_k, query.domain)


class GetSessionHistoryHandler:
    def __init__(self, queries: SessionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetSessionHistoryQuery) -> SessionDto | None:
        return await self._queries.get_session_history(query.session_id)