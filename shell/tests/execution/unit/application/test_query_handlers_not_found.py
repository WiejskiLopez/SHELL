"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

from shell.application.platform.queries.queries import (
    GetCurrentTaskExecutionQuery,
    GetWorkflowQuery,
)
from shell.application.platform.query_handlers.query_handlers import (
    GetCurrentTaskExecutionHandler,
    GetWorkflowHandler,
)
from shell.infrastructure.platform.persistence.memory import InMemoryQueryServices


class TestQueryHandlersNotFound:
    async def test_get_task_not_found(self, queries: InMemoryQueryServices) -> None:
        dto = await GetCurrentTaskExecutionHandler(queries).handle(
            GetCurrentTaskExecutionQuery("missing")
        )
        assert dto is None

    async def test_get_workflow_not_found(self, queries: InMemoryQueryServices) -> None:
        dto = await GetWorkflowHandler(queries).handle(GetWorkflowQuery("no-id"))
        assert dto is None
