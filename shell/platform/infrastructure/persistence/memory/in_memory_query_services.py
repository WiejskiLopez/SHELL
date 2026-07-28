from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.node_execution.dto.node_execution import NodeExecutionDto
from shell.application.execution.task_execution.dto.task_execution import TaskExecutionDto
from shell.application.execution.workflow.dto.workflow import WorkflowDto
from shell.application.session.session.dto.session import SessionDto
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_name import (
    TaskExecutionName,
)
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.infrastructure.execution.graph_execution.persistence.memory.in_memory_graph_execution_repository import (
    InMemoryGraphExecutionRepository,
)
from shell.infrastructure.execution.node_execution.persistence.memory.in_memory_node_execution_repository import (
    InMemoryNodeExecutionRepository,
)
from shell.infrastructure.execution.task_execution.persistence.memory.in_memory_task_execution_repository import (
    InMemoryTaskExecutionRepository,
)
from shell.infrastructure.execution.workflow.persistence.memory.in_memory_workflow_repository import (
    InMemoryWorkflowRepository,
)
from shell.infrastructure.session.session.persistence.memory.in_memory_session_repository import (
    InMemorySessionRepository,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.persistence.memory.in_memory_unit_of_work import (
        InMemoryUnitOfWork,  # noqa: TC002 — InMemoryUnitOfWork używany w konstruktorze InMemoryQueryServices
    )


class InMemoryQueryServices:
    def __init__(self, unit_of_work: InMemoryUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    async def get_task_execution_by_name(self, name: str) -> TaskExecutionDto | None:

        task_execution = await self._unit_of_work.repository(
            InMemoryTaskExecutionRepository
        ).get_by_name(TaskExecutionName(name))
        if not task_execution:
            return None
        graph_executions = await self._unit_of_work.repository(
            InMemoryGraphExecutionRepository
        ).get_by_task_execution_id(task_execution.id)
        node_executions = []
        if graph_executions:
            graph_execution = graph_executions[0]
            nodes = await self._unit_of_work.repository(
                InMemoryNodeExecutionRepository
            ).list_by_graph_execution_id(graph_execution.id)
            node_executions = [
                NodeExecutionDto(
                    id=node_execution.id.value,
                    node_type=node_execution.node_type.value,
                    model=None,
                    command=None,
                )
                for node_execution in nodes
            ]
        return TaskExecutionDto(
            id=task_execution.id.value,
            name=task_execution.name.value,
            created_at=task_execution.created_at.value,
            node_executions=tuple(node_executions),
        )

    async def get_current_task(self, name: str) -> TaskExecutionDto | None:
        return await self.get_task_execution_by_name(name)

    async def get_by_id(self, id: str) -> WorkflowDto | SessionDto | None:
        workflow = await self._unit_of_work.repository(InMemoryWorkflowRepository).get_by_id(
            WorkflowId(id)
        )
        if workflow is not None:
            return WorkflowDto(
                id=str(workflow.id),
                status=workflow.status.value,
                session_id=workflow.session_id.value,
                project_id=workflow.project_id.value,
                created_at=workflow.created_at.value,
            )
        session = await self._unit_of_work.repository(InMemorySessionRepository).get_by_id(
            SessionId(id)
        )
        if session is None:
            return None
        return SessionDto(
            id=session.id.value,
            goal=session.goal,
            status=session._status,
            opened_at=session.opened_at.value,
            closed_at=session.closed_at.value if session.closed_at else None,
            created_at=session.created_at.value,
        )
