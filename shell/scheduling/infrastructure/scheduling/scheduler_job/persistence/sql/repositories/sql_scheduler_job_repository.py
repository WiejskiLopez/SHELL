from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import exists as sa_exists
from sqlalchemy import select

from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.repositories.scheduler_execution_repository import (
    SchedulerExecutionRepository,
)
from shell.scheduling.infrastructure.scheduling.scheduler_job.persistence.sql.mappers import (
    scheduler_job_entity_to_model,
    scheduler_job_model_to_entity,
    scheduler_job_update_model,
)

from ..models import SchedulerJobModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.scheduling.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
        SchedulerDefinitionId,
    )
    from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
        SchedulerExecution,
    )
    from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.value_objects.action_ref import (
        ActionRef,
    )
    from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.value_objects.count_result import (
        CountResult,
    )
    from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.value_objects.execution_status import (
        ExecutionStatus,
    )
    from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
        SchedulerExecutionId,
    )


class SqlSchedulerJobRepository(SchedulerExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: SchedulerExecutionId) -> SchedulerExecution | None:
        query = select(SchedulerJobModel).where(SchedulerJobModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return scheduler_job_model_to_entity(row) if row else None

    async def save(self, execution: SchedulerExecution) -> None:
        model = await self._session.get(SchedulerJobModel, execution.id.value)
        if model is None:
            model = scheduler_job_entity_to_model(execution)
            self._session.add(model)
        else:
            scheduler_job_update_model(model, execution)

    async def delete(self, id: SchedulerExecutionId) -> None:
        model = await self._session.get(SchedulerJobModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: SchedulerExecutionId) -> ExistsResult:
        stmt = select(sa_exists().where(SchedulerJobModel.id == id.value))
        result = await self._session.execute(stmt)
        return ExistsResult(result.scalar() or False)

    async def get_by_action_ref(self, action_ref: ActionRef) -> list[SchedulerExecution]:
        query = select(SchedulerJobModel).where(SchedulerJobModel.action_ref == action_ref.value)
        rows = (await self._session.execute(query)).scalars().all()
        return [scheduler_job_model_to_entity(r) for r in rows if r is not None]

    async def count_by_definition_and_status(
        self, scheduler_definition_id: SchedulerDefinitionId, status: ExecutionStatus
    ) -> CountResult:
        query = select(SchedulerJobModel).where(
            SchedulerJobModel.scheduler_definition_id == scheduler_definition_id.value,
            SchedulerJobModel.status == status.value,
        )
        rows = (await self._session.execute(query)).scalars().all()
        from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.value_objects.count_result import (
            CountResult,
        )

        return CountResult(len(rows))
