from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
        SessionIdRef,
    )
    from shell.execution.domain.execution.aggregates.workflow import Workflow
    from shell.execution.domain.execution.aggregates.workflow.value_objects.workflow_id import (
        WorkflowId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class WorkflowRepository(Protocol):
    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None: ...
    async def get_by_session_id(self, session_id: SessionIdRef) -> list[Workflow]: ...
    async def save(self, workflow: Workflow) -> None: ...
    async def delete(self, id: WorkflowId) -> None: ...
    async def exists(self, id: WorkflowId) -> ExistsResult: ...
