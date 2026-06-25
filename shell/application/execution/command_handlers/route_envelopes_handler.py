"""RouteEnvelopesHandler — routes PENDING envelopes for a workflow."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.envelope.services.envelope_lifecycle_service import (
    EnvelopeLifecycleService,
)
from shell.domain.execution.events import (
    EnvelopeDeadletteredEvent,
    EnvelopeExpiredEvent,
    EnvelopeRoutedEvent,
)
from shell.domain.execution.exceptions import WorkflowNotFound
from shell.domain.execution.services.graph_execution_routing_service import (
    GraphExcetutionRoutingService,
)
from shell.domain.execution.value_objects.ids import WorkflowId
from shell.domain.platform.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus

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
        unit_of_work: UnitOfWork,
        clock: Clock,
        max_step: int = 0,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._max_step = max_step

    async def handle(self, route_envelopes_command: RouteEnvelopesCommand) -> int:
        """Process envelopes and return the number of envelopes routed."""
        workflow_id = WorkflowId(route_envelopes_command.workflow_id)

        async with self._unit_of_work as unit_of_work:
            workflow = await unit_of_work.workflow_repository.get_by_id(workflow_id)
            if workflow is None:
                raise WorkflowNotFound(route_envelopes_command.workflow_id)

            pending = await unit_of_work.envelope_repository.list_pending(workflow_id)
            graph_executions = await unit_of_work.graph_execution_repository.get_by_workflow_id(workflow.id)
            graph_execution = graph_executions[0] if graph_executions else None

            now = self._clock.now()
            routed = 0
            expired = 0

            for envelope in pending:
                new_status = EnvelopeLifecycleService.advance(envelope, self._max_step)
                if new_status == EnvelopeStatus.DEAD:
                    envelope.transition_status(EnvelopeStatus.DEAD, now)
                    await unit_of_work.envelope_repository.save(envelope)
                    unit_of_work.stage_events(
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
                        envelope.deliver_to(target_graph_node_execution_id)
                    except Exception as e:
                        logger.warning(
                            "Envelope %s dead-lettered after routing failure: %s",
                            envelope.id.value,
                            e,
                        )
                        envelope.transition_status(EnvelopeStatus.DEAD, now)
                        await unit_of_work.envelope_repository.save(envelope)
                        unit_of_work.stage_events(
                            [
                                EnvelopeDeadletteredEvent.now(
                                    envelope.id, envelope.workflow_id, reason=str(e), now=now
                                )
                            ]
                        )
                        continue

                envelope.transition_status(EnvelopeStatus.ACTIVE, now)
                envelope.transition_stage(EnvelopeStage.SENT, now)
                await unit_of_work.envelope_repository.save(envelope)
                unit_of_work.stage_events(
                    [EnvelopeRoutedEvent.now(envelope.id, envelope.workflow_id, now=now)]
                )
                routed += 1

        return routed
