"""GraphExecutionRepository port — persistence boundary for the Graph aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_execution.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.task_execution.task_execution_id import TaskExecutionId
    from shell.domain.execution.aggregates.workflow.workflow_id import WorkflowId


class GraphExecutionRepository(Protocol):
    async def get_by_id(self, graph_execution_id: GraphExecutionId) -> GraphExecution | None: ...
    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> GraphExecution | None: ...
    async def get_by_workflow_id(self, workflow_id: WorkflowId) -> list[GraphExecution]: ...
    async def save(self, graph_execution: GraphExecution) -> None: ...
