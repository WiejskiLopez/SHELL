"""SyncWorkflowRunner — runs a full tasker workflow synchronously.

Bootstraps a Workflow (via ``RunTaskerWorkflowHandler``) and then pumps
the outbox → inbox → handler loop until the workflow reaches a terminal
state (``done`` or ``failed``).  Designed for the CLI ``run-tasker``
command so the user experiences a *synchronous* workflow execution from a
single process.

Each iteration of the pump loop corresponds to **one step** (one node
execution), strictly following the one-cycle-per-step principle:

    command/event → execution → next event → (repeat)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.command_handlers.run_tasker_workflow_handler import (
        RunTaskerWorkflowHandler,
    )
    from shell.application.ports.unit_of_work import UnitOfWork
    from shell.infrastructure.messaging.outbox_to_inbox_relay import OutboxToInboxRelay
    from shell.infrastructure.messaging.processor.inbox_processor import InboxProcessor


@dataclass(frozen=True, slots=True)
class SyncWorkflowResult:
    """Result of a synchronous workflow run."""

    workflow_id: str
    status: str
    message: str


class SyncWorkflowRunner:
    """Pumps outbox → inbox → handlers until the workflow is terminal."""

    def __init__(
        self,
        handler: RunTaskerWorkflowHandler,
        relay: OutboxToInboxRelay,
        processor: InboxProcessor,
        uow: UnitOfWork,
    ) -> None:
        self._handler = handler
        self._relay = relay
        self._processor = processor
        self._uow = uow

    async def run(
        self,
        task_execution_id: str,
        work_dir: str,
    ) -> SyncWorkflowResult:
        """Bootstrap the workflow and pump events until terminal.

        Returns the final workflow status and id.
        """
        from shell.application.commands.commands import RunTaskerWorkflowCommand
        from shell.domain.value_objects.ids import WorkflowId
        from shell.domain.value_objects.status import Status

        # Phase 1: Bootstrap — creates workflow + emits first event to outbox
        cmd = RunTaskerWorkflowCommand(
            task_execution_id=task_execution_id,
            work_dir=work_dir,
        )
        workflow_id_str = await self._handler.handle(cmd)
        workflow_id = WorkflowId(workflow_id_str)

        # Phase 2: Pump loop — one cycle per step
        max_iterations = 1000  # safety limit
        for _ in range(max_iterations):
            # Relay: outbox_event → inbox_event
            outbox_count = await self._relay.run_once()
            if outbox_count > 0:
                await self._processor.run_once()
            else:
                await self._processor.run_once()

            # Check workflow status
            async with self._uow as uow:
                workflow = await uow.workflows.get_by_id(workflow_id)
                if workflow is None:
                    return SyncWorkflowResult(
                        workflow_id=workflow_id_str,
                        status="unknown",
                        message="Workflow not found after bootstrap",
                    )
                if workflow.status in (Status.done(), Status.failed()):
                    message = (
                        "Workflow completed successfully"
                        if workflow.status == Status.done()
                        else f"Workflow failed: {workflow.status.value}"
                    )
                    return SyncWorkflowResult(
                        workflow_id=workflow_id_str,
                        status=workflow.status.value,
                        message=message,
                    )

            if outbox_count == 0:
                outbox_count = await self._relay.run_once()
                if outbox_count == 0:
                    break

        # If we get here, the workflow didn't reach terminal within limits
        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(workflow_id)
            status = workflow.status.value if workflow else "unknown"

        return SyncWorkflowResult(
            workflow_id=workflow_id_str,
            status=status,
            message="Workflow did not reach terminal state within iteration limit",
        )
