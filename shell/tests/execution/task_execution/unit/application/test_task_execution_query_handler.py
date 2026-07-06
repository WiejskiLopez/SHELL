"""Unit tests for task_execution query handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.task_execution.queries import TaskExecutionGetCurrentQuery
from shell.application.execution.task_execution.query_handlers.task_execution_get_current_handler import (
    TaskExecutionGetCurrentHandler,
)

if TYPE_CHECKING:
    from shell.infrastructure.platform.persistence.memory import (
        InMemoryQueryServices,  # noqa: TC002 -- used in TYPE_CHECKING block only, needed for pytest fixture type annotation
    )


class TestTaskExecutionQueryHandler:
    async def test_get_task_not_found(self, queries: InMemoryQueryServices) -> None:
        dto = await TaskExecutionGetCurrentHandler(queries).handle(
            TaskExecutionGetCurrentQuery("missing")
        )
        assert dto is None
