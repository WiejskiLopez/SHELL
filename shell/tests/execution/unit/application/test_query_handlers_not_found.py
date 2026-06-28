"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

from shell.application.platform.queries.queries import (
    TaskExecutionGetCurrentQuery,
    WorkflowGetByIdQuery,
)
from shell.application.platform.query_handlers import (
    TaskExecutionGetCurrentHandler,
    WorkflowGetByIdHandler,
)
from shell.infrastructure.platform.persistence.memory import (
    InMemoryQueryServices,  # noqa: TC002 — InMemoryQueryServices używany w sygnaturach fixture'ów pytest
)


class TestQueryHandlersNotFound:
    async def test_get_task_not_found(self, queries: InMemoryQueryServices) -> None:
        dto = await TaskExecutionGetCurrentHandler(queries).handle(
            TaskExecutionGetCurrentQuery("missing")
        )
        assert dto is None

    async def test_get_workflow_not_found(self, queries: InMemoryQueryServices) -> None:
        dto = await WorkflowGetByIdHandler(queries).handle(WorkflowGetByIdQuery("no-id"))
        assert dto is None
