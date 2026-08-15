from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.application.execution.node_execution.dto.node_execution import (
    NodeExecutionDto,
)
from shell.execution_service.application.execution.task_execution.dto.task_execution import (
    TaskExecutionDto,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_name import (
    TaskExecutionName,
)
from shell.execution_service.infrastructure.execution.graph_execution.persistence.memory.in_memory_graph_execution_repository import (
    InMemoryGraphExecutionRepository,
)
from shell.execution_service.infrastructure.execution.node_execution.persistence.memory.in_memory_node_execution_repository import (
    InMemoryNodeExecutionRepository,
)
from shell.execution_service.infrastructure.execution.task_execution.persistence.memory.in_memory_task_execution_repository import (
    InMemoryTaskExecutionRepository,
)

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.task_execution.task_execution import (
        TaskExecution,
    )
    from shell.execution_service.infrastructure.execution.persistence.memory.unit_of_work import (
        InMemoryExecutionUnitOfWork,
    )


class InMemoryExecutionQueryService:
    def __init__(self, unit_of_work: InMemoryExecutionUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    async def get_by_id(self, task_execution_id: str) -> TaskExecutionDto | None:
        task_execution = await self._unit_of_work.repository(
            InMemoryTaskExecutionRepository
        ).get_current_by_id(TaskExecutionId(task_execution_id))
        if not task_execution:
            return None
        return await self._build_task_execution_dto(task_execution)

    async def get_task_execution_by_name(self, name: str) -> TaskExecutionDto | None:
        task_execution = await self._unit_of_work.repository(
            InMemoryTaskExecutionRepository
        ).get_by_name(TaskExecutionName(name))
        if not task_execution:
            return None
        return await self._build_task_execution_dto(task_execution)

    async def get_current_task(self, name: str) -> TaskExecutionDto | None:
        return await self.get_task_execution_by_name(name)

    async def _build_task_execution_dto(self, task_execution: TaskExecution) -> TaskExecutionDto:
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
