from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import exists as sa_exists
from sqlalchemy import select

from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.repositories.scheduler_execution_repository import (
    SchedulerExecutionRepository,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_execution.persistence.sql.mappers import (
    scheduler_execution_entity_to_model,
    scheduler_execution_model_to_entity,
    scheduler_execution_update_model,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (
    SchedulerExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
        SchedulerDefinitionId,
    )
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
        SchedulerExecution,
    )
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.action_ref import (
        ActionRef,
    )
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.count_result import (
        CountResult,
    )
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.execution_status import (
        ExecutionStatus,
    )
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
        SchedulerExecutionId,
    )


class SqlSchedulerExecutionRepository(SchedulerExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: SchedulerExecutionId) -> SchedulerExecution | None:
        query = select(SchedulerExecutionModel).where(SchedulerExecutionModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return scheduler_execution_model_to_entity(row) if row else None

    async def save(self, execution: SchedulerExecution) -> None:
        model = await self._session.get(SchedulerExecutionModel, execution.id.value)
        if model is None:
            model = scheduler_execution_entity_to_model(execution)
            self._session.add(model)
        else:
            scheduler_execution_update_model(model, execution)

    async def delete(self, id: SchedulerExecutionId) -> None:
        model = await self._session.get(SchedulerExecutionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: SchedulerExecutionId) -> ExistsResult:
        stmt = select(sa_exists().where(SchedulerExecutionModel.id == id.value))
        result = await self._session.execute(stmt)
        return ExistsResult(result.scalar() or False)

    async def get_by_action_ref(self, action_ref: ActionRef) -> list[SchedulerExecution]:
        query = select(SchedulerExecutionModel).where(
            SchedulerExecutionModel.action_ref == action_ref.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [scheduler_execution_model_to_entity(r) for r in rows if r is not None]

    async def count_by_definition_and_status(
        self, scheduler_definition_id: SchedulerDefinitionId, status: ExecutionStatus
    ) -> CountResult:
        query = select(SchedulerExecutionModel).where(
            SchedulerExecutionModel.scheduler_definition_id == scheduler_definition_id.value,
            SchedulerExecutionModel.status == status.value,
        )
        rows = (await self._session.execute(query)).scalars().all()
        from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.count_result import (
            CountResult,
        )

        return CountResult(len(rows))
