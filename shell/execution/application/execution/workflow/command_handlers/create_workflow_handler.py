from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.domain.execution.aggregates.session_execution.value_objects.project_id_ref import (
    ProjectIdRef,
)
from shell.execution.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.execution.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.execution.domain.execution.aggregates.workflow.value_objects.workflow_id import (
    WorkflowId,
)
from shell.execution.domain.execution.aggregates.workflow.workflow import Workflow
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.execution.application.execution.workflow.commands.create_workflow_command import (
        CreateWorkflowCommand,
    )
    from shell.platform.application.ports.identity import IdGenerator
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class CreateWorkflowHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: CreateWorkflowCommand) -> str:
        now = CreatedAt.from_datetime(self._clock.now())
        workflow_id = self._id_generator.new_id(WorkflowId)

        session_id = SessionIdRef(command.session_id)
        project_id = ProjectIdRef(command.project_id)
        workflow = Workflow.create(
            id_=workflow_id,
            now=now,
            session_id=session_id,
            project_id=project_id,
        )

        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(WorkflowRepository, workflow)

        return workflow_id.value
