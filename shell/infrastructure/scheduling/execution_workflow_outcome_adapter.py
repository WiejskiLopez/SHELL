"""Adapter: subscribes to execution domain events and delegates to scheduling WorkflowOutcomeReceiver.

This adapter lives in infrastructure/ because its job is to bridge two domains:
it listens to events from `shell.domain.execution` and forwards them to a
`WorkflowOutcomeReceiver` port defined in `shell.domain.scheduling`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from shell.domain.execution.events import WorkflowCompletedEvent, WorkflowFailedEvent

if TYPE_CHECKING:
    from shell.domain.scheduling.ports.workflow_outcome_receiver import WorkflowOutcomeReceiver


class ExecutionWorkflowOutcomeAdapter:
    def __init__(self, receiver: WorkflowOutcomeReceiver) -> None:
        self._receiver = receiver

    async def handle(self, event: Union[WorkflowCompletedEvent, WorkflowFailedEvent]) -> None:
        if isinstance(event, WorkflowCompletedEvent):
            await self._receiver.on_workflow_completed(event.workflow_id.value)
        elif isinstance(event, WorkflowFailedEvent):
            await self._receiver.on_workflow_failed(event.workflow_id.value, event.error or "workflow_failed")
