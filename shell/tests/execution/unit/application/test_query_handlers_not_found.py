"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

from shell.application.execution.queries.task_execution_queries import TaskExecutionGetCurrentQuery
from shell.application.execution.queries.workflow_get_by_id_query import WorkflowGetByIdQuery
from shell.application.execution.query_handlers.task_execution_get_current_handler import TaskExecutionGetCurrentHandler
from shell.application.execution.query_handlers.workflow_get_by_id_handler import WorkflowGetByIdHandler
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
