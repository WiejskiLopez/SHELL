"""Porty dla ścieżki odczytu (CQRS). Zwracają bezpośrednio DTO."""

from typing import Protocol

from shell.application.dto.dto import (
    EnvelopeDto,
    GraphDefinitionDto,
    GraphNodeExecutionResultDto,
    PromptDto,
    RagChunkDto,
    RunnerConfigDto,
    SessionDto,
    TaskExecutionDto,
    WorkflowDto,
)


class TaskExecutionQueryService(Protocol):
    """Port do bezpośredniego odczytu DTO zadań (omija domenę)."""

    async def get_task_execution_by_name(self, name: str) -> TaskExecutionDto | None: ...

    async def get_current_task(self, name: str) -> TaskExecutionDto | None: ...


class WorkflowQueryService(Protocol):
    """Port do pobierania stanu workflow."""

    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None: ...


class EnvelopeQueryService(Protocol):
    """Port do listowania kopert (np. dla routera)."""

    async def get_envelopes_by_workflow(
        self, workflow_id: str, pending_only: bool = False
    ) -> list[EnvelopeDto]: ...


class GraphNodeExecutionResultQueryService(Protocol):
    """Port do sprawdzania wyników wykonania konkretnych węzłów."""

    async def get_graph_node_execution_result(self, graph_node_execution_id: str, workflow_id: str) -> GraphNodeExecutionResultDto | None: ...


class PromptQueryService(Protocol):
    """Port do pobierania treści promptów."""

    async def get_prompt(self, name: str) -> PromptDto | None: ...


class RunnerConfigQueryService(Protocol):
    """Port do pobierania konfiguracji dla runnerów."""

    async def get_runner_config(self, package_name: str) -> RunnerConfigDto | None: ...


class RagQueryService(Protocol):
    """Port do wyszukiwania semantycznego (RAG)."""

    async def search_similar(
        self, query_embedding: bytes, top_k: int = 5, domain: str | None = None
    ) -> list[RagChunkDto]: ...


class SessionQueryService(Protocol):
    """Port do pobierania historii sesji/czatu."""

    async def get_session_history(self, session_id: str) -> SessionDto | None: ...


class GraphDefinitionQueryService(Protocol):
    """Port do pobierania historii sesji/czatu."""

    async def get_graph_definition_by_name(self, name: str) -> GraphDefinitionDto | None: ...
