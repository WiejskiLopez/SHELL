"""GraphExecutionRepository port — persistence boundary for the Graph aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.execution.value_objects.exists_result import ExistsResult


class GraphExecutionRepository(Protocol):
    async def get_by_id(self, graph_execution_id: GraphExecutionId) -> GraphExecution | None: ...
    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> list[GraphExecution]: ...
    async def get_by_workflow_id(self, workflow_id: WorkflowId) -> list[GraphExecution]: ...
    async def get_by_parent_id(
        self, parent_graph_execution_id: GraphExecutionId
    ) -> list[GraphExecution]: ...
    async def get_main_rounds(
        self, task_execution_id: TaskExecutionId
    ) -> list[GraphExecution]: ...
    async def save(self, graph_execution: GraphExecution) -> None: ...
    async def delete(self, id: GraphExecutionId) -> None: ...
    async def exists(self, id: GraphExecutionId) -> ExistsResult: ...
    