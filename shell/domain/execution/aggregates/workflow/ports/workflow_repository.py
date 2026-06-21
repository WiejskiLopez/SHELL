from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.aggregates.workflow.workflow_id import WorkflowId


class WorkflowRepository(Protocol):
    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None: ...
    async def save(self, workflow: Workflow) -> None: ...
