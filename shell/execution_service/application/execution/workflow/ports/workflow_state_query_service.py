from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution_service.application.execution.workflow.dto.workflow_state import (
        WorkflowStateDto,
    )


class WorkflowStateQueryService(Protocol):
    async def get_by_id(self, workflow_state_id: str) -> WorkflowStateDto | None: ...
