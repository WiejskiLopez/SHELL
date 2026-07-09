"""Unit tests for workflow query handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.workflow.queries.get_workflow_by_id_query import (
    GetWorkflowByIdQuery,
)
from shell.application.execution.workflow.query_handlers.get_workflow_by_id_handler import (
    GetWorkflowByIdHandler,
)

if TYPE_CHECKING:
    from shell.infrastructure.platform.persistence.memory import (
        InMemoryQueryServices,  # noqa: TC002 -- used in TYPE_CHECKING block only, needed for pytest fixture type annotation
    )


class TestWorkflowQueryHandler:
    async def test_get_workflow_not_found(self, queries: InMemoryQueryServices) -> None:
        dto = await GetWorkflowByIdHandler(queries).handle(GetWorkflowByIdQuery("no-id"))
        assert dto is None
