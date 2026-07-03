from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shell.domain.platform.ports.log import Logger
    from shell.domain.session.aggregates.session.events.event import (
        SessionOpenedEvent,
    )
    from shell.domain.session.ports.workflow_session_provider import (
        WorkflowSessionProvider,
    )


class PropagateSessionOutputToWorkflowInput:
    def __init__(
        self,
        workflow_session_provider: WorkflowSessionProvider,
        logger: Logger,
    ) -> None:
        self._workflow_session_provider = workflow_session_provider
        self._logger = logger

    async def handle(self, event: SessionOpenedEvent) -> None:
        session_payload: dict[str, Any] = {
            "session_id": event.session_id.value,
            "user_id": event.user_id.value,
            "project_id": event.project_id.value,
        }
        await self._workflow_session_provider.add_session_output(
            session_id=event.session_id.value,
            user_id=event.user_id.value,
            project_id=event.project_id.value,
            payload=session_payload,
        )
