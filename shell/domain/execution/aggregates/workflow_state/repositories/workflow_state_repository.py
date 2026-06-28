from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
        WorkflowStateId,
    )
    from shell.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState
    from shell.domain.platform.value_objects.exists_result import ExistsResult
    from shell.domain.platform.value_objects.state_direction import StateDirection


class WorkflowStateRepository(Protocol):
    async def get_by_id(self, id_: WorkflowStateId) -> WorkflowState | None: ...

    async def list_by_workflow_id(self, workflow_id: WorkflowId) -> list[WorkflowState]: ...

    async def list_by_workflow_id_and_direction(
        self, workflow_id: WorkflowId, direction: StateDirection
    ) -> list[WorkflowState]: ...

    async def save(self, workflow_state: WorkflowState) -> None: ...

    async def delete(self, id_: WorkflowStateId) -> None: ...

    async def exists(self, id_: WorkflowStateId) -> ExistsResult: ...
