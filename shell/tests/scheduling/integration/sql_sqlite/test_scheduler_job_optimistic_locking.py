"""Optimistic locking tests for SchedulerJob aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.domain.scheduling.aggregates.scheduler_job.scheduler_job import SchedulerJob
from shell.domain.scheduling.value_objects.ids import SchedulerDefinitionId, SchedulerExecutionId
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSchedulerJobOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        uow1 = SqlAlchemyUnitOfWork(session_factory)
        uow2 = SqlAlchemyUnitOfWork(session_factory)
        sj_id = SchedulerExecutionId.generate()
        sd_id = SchedulerDefinitionId.generate()

        async with uow1 as u:
            entity = SchedulerJob(id=sj_id, scheduler_definition_id=sd_id, name="v1")
            await u.scheduler_execution_repository.save(entity)
            await u.commit()

        async with uow1 as u1:
            entity_a = await u1.scheduler_execution_repository.get_by_id(sj_id)
            assert entity_a is not None

            async with uow2 as u2:
                entity_b = await u2.scheduler_execution_repository.get_by_id(sj_id)
                assert entity_b is not None

                modified_a = SchedulerJob(id=sj_id, scheduler_definition_id=sd_id, name="v2")
                await u1.scheduler_execution_repository.save(modified_a)
                await u1.commit()

                modified_b = SchedulerJob(id=sj_id, scheduler_definition_id=sd_id, name="v3")
                await u2.scheduler_execution_repository.save(modified_b)
                with pytest.raises(ConcurrentModificationError):
                    await u2.commit()
