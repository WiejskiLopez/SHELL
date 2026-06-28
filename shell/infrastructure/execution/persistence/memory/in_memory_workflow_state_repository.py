from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow_state.repositories.workflow_state_repository import (
    WorkflowStateRepository,
)
from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.domain.execution.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState


class InMemoryWorkflowStateRepository(WorkflowStateRepository):
    def __init__(self) -> None:
        self._store: dict[str, WorkflowState] = {}

    async def get_by_id(self, id_: WorkflowStateId) -> WorkflowState | None:
        item = self._store.get(id_.value)
        return copy.deepcopy(item) if item is not None else None

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

    async def save(self, workflow_state: WorkflowState) -> None:
        self._store[workflow_state.id.value] = copy.deepcopy(workflow_state)

    async def delete(self, id_: WorkflowStateId) -> None:
        self._store.pop(id_.value, None)

    async def exists(self, id_: WorkflowStateId) -> bool:
        return id_.value in self._store
