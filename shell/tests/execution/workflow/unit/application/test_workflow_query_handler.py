"""Unit tests for workflow query handlers."""

from __future__ import annotations

from typing import Any

from shell.execution.application.execution.workflow.queries.get_workflow_by_id_query import (
    GetWorkflowByIdQuery,
)
from shell.execution.application.execution.workflow.query_handlers.get_workflow_by_id_handler import (
    GetWorkflowByIdHandler,
)


class TestWorkflowQueryHandler:
    async def test_get_workflow_not_found(self, queries: Any) -> None:
        dto = await GetWorkflowByIdHandler(queries).handle(GetWorkflowByIdQuery("no-id"))
        assert dto is None
