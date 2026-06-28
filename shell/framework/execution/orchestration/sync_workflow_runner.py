"""SyncWorkflowRunner — runs a full tasker workflow synchronously.

Bootstraps a Workflow (via ``RunTaskerWorkflowHandler``) and then pumps
the outbox -> inbox -> handler loop until the workflow reaches a terminal
state (``done`` or ``failed``).  Designed for the CLI ``run-tasker``
command so the user experiences a *synchronous* workflow execution from a
single process.

Each iteration of the pump loop corresponds to **one step** (one node
execution), strictly following the one-cycle-per-step principle:

    command/event -> execution -> next event -> (repeat)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)

if TYPE_CHECKING:
    from shell.application.execution.command_handlers.workflow_run_tasker_handler import (
        WorkflowRunTaskerHandler,
    )
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.infrastructure.platform.messaging.event.outbox_to_inbox_relay import (
        OutboxToInboxRelay,
    )
    from shell.infrastructure.platform.messaging.event.processor.inbox_processor import (
        InboxProcessor,
    )

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SyncWorkflowResult:
    """Result of a synchronous workflow run."""

    workflow_id: str
    status: str
    message: str
    iterations: int = 0
    elapsed_seconds: float = 0.0
    total_outbox_processed: int = 0
    total_inbox_processed: int = 0


@dataclass(slots=True)
class _PumpMetrics:
    outbox_total: int = 0
    inbox_total: int = 0
    idle_consecutive: int = 0


class SyncWorkflowRunner:
    """Pumps outbox -> inbox -> handlers until the workflow is terminal."""

    def __init__(
        self,
        handler: WorkflowRunTaskerHandler,
        relay: OutboxToInboxRelay,
        processor: InboxProcessor,
        unit_of_work: UnitOfWork,
        max_iterations: int = 1000,
        max_timeout: float = 300.0,
        max_idle_before_break: int = 10,
    ) -> None:
        self._handler = handler
        self._relay = relay
        self._processor = processor
        self._unit_of_work = unit_of_work
        self._max_iterations = max_iterations
        self._max_timeout = max_timeout
        self._max_idle_before_break = max_idle_before_break

    async def run(
        self,
        task_execution_id: str,
        work_dir: str,
    ) -> SyncWorkflowResult:
        from shell.application.execution.commands.workflow_commands import RunTaskerWorkflowCommand
        from shell.domain.execution.value_objects.ids import WorkflowId
        from shell.domain.execution.value_objects.workflow_status import WorkflowStatus

        start_time = time.monotonic()

        cmd = RunTaskerWorkflowCommand(
            task_execution_id=task_execution_id,
            work_dir=work_dir,
        )
        workflow_id_str = await self._handler.handle(cmd)
        workflow_id = WorkflowId(workflow_id_str)

        metrics = _PumpMetrics()

        for iteration in range(self._max_iterations):
            elapsed = time.monotonic() - start_time
            if elapsed > self._max_timeout:
                logger.warning(
                    "Workflow %s exceeded max timeout %.1fs after %d iterations",
                    workflow_id_str,
                    self._max_timeout,
                    iteration,
                )
                break

            try:
                outbox_count = await self._relay.run_once()
                inbox_count = await self._processor.run_once()
            except Exception:
                logger.exception("Pump iteration %d failed, continuing...", iteration)
                continue

            metrics.outbox_total += outbox_count
            metrics.inbox_total += inbox_count

            if outbox_count == 0 and inbox_count == 0:
                metrics.idle_consecutive += 1
                if metrics.idle_consecutive >= self._max_idle_before_break:
                    logger.info(
                        "Workflow %s idle for %d consecutive iterations, breaking",
                        workflow_id_str,
                        metrics.idle_consecutive,
                    )
                    break
            else:
                metrics.idle_consecutive = 0

            async with self._unit_of_work as unit_of_work:
                workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(workflow_id)
                if workflow is None:
                    elapsed = time.monotonic() - start_time
                    return SyncWorkflowResult(
                        workflow_id=workflow_id_str,
                        status="unknown",
                        message="Workflow not found after bootstrap",
                        iterations=iteration + 1,
                        elapsed_seconds=elapsed,
                        total_outbox_processed=metrics.outbox_total,
                        total_inbox_processed=metrics.inbox_total,
                    )
                if workflow.status in (WorkflowStatus.COMPLETED, WorkflowStatus.ABORTED):
                    elapsed = time.monotonic() - start_time
                    message = (
                        "Workflow completed successfully"
                        if workflow.status == WorkflowStatus.COMPLETED
                        else f"Workflow failed: {workflow.status.value}"
                    )
                    return SyncWorkflowResult(
                        workflow_id=workflow_id_str,
                        status=workflow.status.value,
                        message=message,
                        iterations=iteration + 1,
                        elapsed_seconds=elapsed,
                        total_outbox_processed=metrics.outbox_total,
                        total_inbox_processed=metrics.inbox_total,
                    )

        elapsed = time.monotonic() - start_time
        async with self._unit_of_work as unit_of_work:
            workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(workflow_id)
            status = workflow.status.value if workflow else "unknown"

        return SyncWorkflowResult(
            workflow_id=workflow_id_str,
            status=status,
            message="Workflow did not reach terminal state within iteration/time limit",
            iterations=self._max_iterations,
            elapsed_seconds=elapsed,
            total_outbox_processed=metrics.outbox_total,
            total_inbox_processed=metrics.inbox_total,
        )
