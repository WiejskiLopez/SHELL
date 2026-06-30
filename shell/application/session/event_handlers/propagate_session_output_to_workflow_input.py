from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.value_objects.session_id_ref import SessionIdRef

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock
    from shell.domain.session.aggregates.session.events.session_opened_event import (
        SessionOpenedEvent,
    )


class PropagateSessionOutputToWorkflowInput:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        logger: Logger,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._logger = logger

    async def handle(self, session_opened_event: SessionOpenedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            workflows = await unit_of_work.repository(WorkflowRepository).get_by_session_id(
                SessionIdRef(session_opened_event.session_id.value)
            )
            if not workflows:
                self._logger.warning(
                    "propagate_session_output_to_workflow_input.no_workflows",
                    session_id=session_opened_event.session_id.value,
                )
                return

            now = self._clock.now()
            session_payload: dict[str, Any] = {
                "session_id": session_opened_event.session_id.value,
                "user_id": session_opened_event.user_id.value,
                "project_id": session_opened_event.project_id.value,
            }
            for workflow in workflows:
                workflow.add_state_input(session_payload, now)  # type: ignore[attr-defined]
                await unit_of_work.repository(WorkflowRepository).save(workflow)
                unit_of_work.stage_events(workflow.pull_events())
