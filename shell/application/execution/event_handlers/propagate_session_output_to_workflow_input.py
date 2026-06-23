from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.session.events.session_opened_event import (
    SessionOpenedEvent,
)

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.logging import Logger
    from shell.application.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork


class PropagateSessionOutputToWorkflowInput:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        logger: Logger,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._logger = logger

    async def handle(self, event: SessionOpenedEvent) -> None:
        async with self._uow as uow:
            workflows = await uow.workflows.get_by_session_id(event.session_id)
            if not workflows:
                self._logger.warning(
                    "propagate_session_output_to_workflow_input.no_workflows",
                    session_id=event.session_id.value,
                )
                return

            now = self._clock.now()
            session_payload: dict[str, Any] = {
                "session_id": event.session_id.value,
                "user_id": event.user_id.value,
                "project_id": event.project_id.value,
            }
            for workflow in workflows:
                workflow.add_state_input(session_payload, now)
                await uow.workflows.save(workflow)
                uow.stage_events(workflow.pull_events())
