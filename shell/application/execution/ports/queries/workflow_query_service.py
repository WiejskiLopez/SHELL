from __future__ import annotations

from typing import Protocol

from shell.application.platform.dto import WorkflowDto


class WorkflowQueryService(Protocol):
    """Port do pobierania stanu workflow."""

    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None: ...
