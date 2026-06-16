"""RouteEnvelopesHandler — routes PENDING envelopes for a workflow."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.events.events import EnvelopeExpired, EnvelopeRouted
from shell.domain.exceptions import WorkflowNotFound
from shell.domain.services.envelope_lifecycle_service import EnvelopeLifecycleService
from shell.domain.services.graph_routing_service import GraphRoutingService
from shell.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell.domain.value_objects.ids import TaskId, WorkflowId

if TYPE_CHECKING:
    from shell.application.commands.commands import RouteEnvelopesCommand
    from shell.application.ports.ports import Clock, UnitOfWork


class RouteEnvelopesHandler:
    """Routes PENDING envelopes to the correct receiver_node_id using the task graph.

    - Envelopes exceeding max_step are expired (DEAD).
    - Remaining PENDING envelopes are resolved to a receiver and moved to ACTIVE.
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
            task = await uow.tasks.get_current_by_id(TaskId(workflow.task_id))
            graph = await uow.graphs.get_by_task_id(task.id) if task is not None else None

            now = self._clock.now()
            routed = 0

            for envelope in pending:
                new_status = EnvelopeLifecycleService.advance(envelope, self._max_step)
                if new_status == EnvelopeStatus.DEAD:
                    envelope.transition_status(EnvelopeStatus.DEAD, now)
                    await uow.envelopes.save(envelope)
                    uow.stage_events([EnvelopeExpired.now(envelope.id, envelope.workflow_id, now=now)])
                    continue

                if graph is not None:
                    try:
                        target_node_id = GraphRoutingService.resolve_target_node(
                            graph,
                            envelope.sender_node_id,
                            envelope.target_role or None,
                        )
                        envelope.receiver_node_id = target_node_id
                    except Exception:
                        continue  # Unresolvable — leave PENDING

                envelope.transition_status(EnvelopeStatus.ACTIVE, now)
                envelope.transition_stage(EnvelopeStage.SENT, now)
                await uow.envelopes.save(envelope)
                uow.stage_events([EnvelopeRouted.now(envelope.id, envelope.workflow_id, now=now)])
                routed += 1

            await uow.commit()

        return routed
