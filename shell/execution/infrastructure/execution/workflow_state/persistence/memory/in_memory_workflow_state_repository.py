from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.execution.domain.execution.aggregates.workflow_state.repositories.workflow_state_repository import (
    WorkflowStateRepository,
)
from shell.execution.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.execution.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState
from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.workflow.value_objects.workflow_id import (
        WorkflowId,
    )
    from shell.platform.domain.value_objects.state_direction import StateDirection


class InMemoryWorkflowStateRepository(
    InMemoryRepository[WorkflowState, WorkflowStateId], WorkflowStateRepository
):
    async def list_by_workflow_id(self, workflow_id: WorkflowId) -> list[WorkflowState]:
        return [
            copy.deepcopy(item) for item in self._store.values() if item.workflow_id == workflow_id
        ]

    async def list_by_workflow_id_and_direction(
        self, workflow_id: WorkflowId, direction: StateDirection
    ) -> list[WorkflowState]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.workflow_id == workflow_id and item.direction == direction
        ]

    async def exists(self, id_: WorkflowStateId) -> ExistsResult:
        return ExistsResult(id_.value in self._store)
