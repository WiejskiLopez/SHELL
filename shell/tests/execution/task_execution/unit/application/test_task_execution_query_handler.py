"""Unit tests for task_execution query handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.application.execution.task_execution.queries import (
    GetTaskExecutionCurrentQuery,
)
from shell.execution.application.execution.task_execution.query_handlers.get_task_execution_current_handler import (
    GetTaskExecutionCurrentHandler,
)

if TYPE_CHECKING:
    from shell.execution.infrastructure.execution.persistence.memory.query_services import (
        InMemoryExecutionQueryService,  # noqa: TC002 -- used in TYPE_CHECKING block only, needed for pytest fixture type annotation
    )


class TestTaskExecutionQueryHandler:
    async def test_get_task_not_found(self, queries: InMemoryExecutionQueryService) -> None:
        dto = await GetTaskExecutionCurrentHandler(queries).handle(  # type: ignore[arg-type]
            GetTaskExecutionCurrentQuery("missing")
        )
        assert dto is None
