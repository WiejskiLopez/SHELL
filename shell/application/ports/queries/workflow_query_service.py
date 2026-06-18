from typing import Protocol

from shell.application.dto.dto import WorkflowDto


class WorkflowQueryService(Protocol):
    """Port do pobierania stanu workflow."""

    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None: ...
