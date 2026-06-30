from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.execution.dto.workflow import WorkflowDto


class WorkflowQueryService(Protocol):
    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None: ...
