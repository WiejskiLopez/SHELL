from __future__ import annotations

import copy

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow_state.repositories.workflow_state_repository import (
    WorkflowStateRepository,
)
from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.domain.execution.value_objects.state_direction import StateDirection
from shell.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryWorkflowStateRepository(InMemoryRepository[WorkflowState, WorkflowStateId], WorkflowStateRepository):

    async def list_by_workflow_id(self, workflow_id: WorkflowId) -> list[WorkflowState]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.workflow_id == workflow_id
        ]

    async def list_by_workflow_id_and_direction(
        self, workflow_id: WorkflowId, direction: StateDirection
    ) -> list[WorkflowState]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.workflow_id == workflow_id and item.direction == direction
        ]

    async def exists(self, id_: WorkflowStateId) -> bool:
        return id_.value in self._store
