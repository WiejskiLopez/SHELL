"""Czyste handlery zapytań (CQRS) — omijają domenę i używają serwisów odczytu."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.dto.dto import (
        EnvelopeDto,
        GraphNodeExecutionResultDto,
        PromptDto,
        RagChunkDto,
        RunnerConfigDto,
        SessionDto,
        TaskExecutionDto,
        WorkflowDto,
    )
    from shell.application.ports.queries import (
        EnvelopeQueryService,
        GraphNodeExecutionResultQueryService,
        PromptQueryService,
        RagQueryService,
        RunnerConfigQueryService,
        SessionQueryService,
        TaskExecutionQueryService,
        WorkflowQueryService,
    )
    from shell.application.queries.queries import (
        GetCurrentTaskExecutionQuery,
        GetEnvelopesByWorkflowQuery,
        GetGraphNodeExecutionResultQuery,
        GetPromptQuery,
        GetRunnerConfigQuery,
        GetSessionHistoryQuery,
        GetTaskExecutionByNameQuery,
        GetWorkflowQuery,
        SearchSimilarQuery,
    )
    from shell.domain.services.rag_index_service import Embedder


class GetTaskExecutionByNameHandler:
    def __init__(self, queries: TaskExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetTaskExecutionByNameQuery) -> TaskExecutionDto | None:
        return await self._queries.get_task_execution_by_name(query.name)


class GetCurrentTaskExecutionHandler:
    def __init__(self, queries: TaskExecutionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetCurrentTaskExecutionQuery) -> TaskExecutionDto | None:
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
        return await self._queries.get_envelopes_by_workflow(query.workflow_id, query.pending_only)


class GetGraphNodeExecutionResultHandler:
    def __init__(self, queries: GraphNodeExecutionResultQueryService) -> None:
        self._queries = queries

    async def handle(
        self, query: GetGraphNodeExecutionResultQuery
    ) -> GraphNodeExecutionResultDto | None:
        return await self._queries.get_graph_node_execution_result(
            query.graph_node_execution_id, query.workflow_id
        )


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
        import struct

        vector = self._embedder.embed_text(query.query_text)
        vector_bytes = struct.pack(f"{len(vector)}f", *vector)
        return await self._queries.search_similar(vector_bytes, query.top_k, query.domain)


class GetSessionHistoryHandler:
    def __init__(self, queries: SessionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetSessionHistoryQuery) -> SessionDto | None:
        return await self._queries.get_session_history(query.session_id)
