"""RouteEnvelopesHandler — routes PENDING envelopes for a workflow."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shell.domain.execution.events import EnvelopeDeadletteredEvent, EnvelopeExpiredEvent, EnvelopeRoutedEvent
from shell.domain.exceptions import WorkflowNotFound
from shell.domain.execution.services.envelope_lifecycle_service import EnvelopeLifecycleService
from shell.domain.execution.services.graph_execution_routing_service import GraphExcetutionRoutingService
from shell.domain.platform.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell.domain.platform.value_objects.ids import WorkflowId

if TYPE_CHECKING:
    from shell.application.platform.commands.commands import RouteEnvelopesCommand
    from shell.application.platform.ports.ports import Clock, UnitOfWork

logger = logging.getLogger(__name__)


class RouteEnvelopesHandler:
    """Routes PENDING envelopes using the task graph to the correct receiver node.

    - Envelopes exceeding max_step are expired (DEAD).
    - Remaining PENDING envelopes are resolved to a receiver and moved to ACTIVE.
    - Envelopes that fail routing are dead-lettered.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        max_step: int = 0,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._max_step = max_step

    async def handle(self, cmd: RouteEnvelopesCommand) -> int:
        """Process envelopes and return the number of envelopes routed."""
        wf_id = WorkflowId(cmd.workflow_id)

        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(wf_id)
            if workflow is None:
                raise WorkflowNotFound(cmd.workflow_id)

            pending = await uow.envelopes.list_pending(wf_id)
            task_execution = await uow.task_executions.get_current_by_id(workflow.task_execution_id)
            graph_execution = (
                await uow.graph_executions.get_by_task_execution_id(task_execution.id)
                if task_execution is not None
                else None
            )

            now = self._clock.now()
            routed = 0
            expired = 0

            for envelope in pending:
                new_status = EnvelopeLifecycleService.advance(envelope, self._max_step)
                if new_status == EnvelopeStatus.DEAD:
                    envelope.transition_status(EnvelopeStatus.DEAD, now)
                    await uow.envelopes.save(envelope)
                    uow.stage_events(
                        [EnvelopeExpiredEvent.now(envelope.id, envelope.workflow_id, now=now)]
                    )
                    expired += 1
                    continue

                if graph_execution is not None:
                    try:
                        target_graph_node_execution_id = (
                            GraphExcetutionRoutingService.resolve_target_graph_node_execution(
                                graph_execution,
                                envelope.sender_graph_node_execution_id,
                                envelope.target_role or None,
                            )
                        )
                        envelope.receiver_graph_node_execution_id = target_graph_node_execution_id
                    except Exception as e:
                        logger.warning(
                            "Envelope %s dead-lettered after routing failure: %s",
                            envelope.id.value, e,
                        )
                        envelope.transition_status(EnvelopeStatus.DEAD, now)
                        await uow.envelopes.save(envelope)
                        uow.stage_events(
                            [EnvelopeDeadletteredEvent.now(
                                envelope.id, envelope.workflow_id, reason=str(e), now=now
                            )]
                        )
                        continue

                envelope.transition_status(EnvelopeStatus.ACTIVE, now)
                envelope.transition_stage(EnvelopeStage.SENT, now)
                await uow.envelopes.save(envelope)
                uow.stage_events([EnvelopeRoutedEvent.now(envelope.id, envelope.workflow_id, now=now)])
                routed += 1

        return routed
