from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution.application.execution.workflow.dto.workflow import WorkflowDto


class WorkflowQueryService(Protocol):
    """Port do pobierania stanu workflow."""

    async def get_by_id(self, workflow_id: str) -> WorkflowDto | None: ...

    async def list_all(
        self, *, page: int = 1, page_size: int = 100, status: str | None = None
    ) -> tuple[list[WorkflowDto], int]: ...
