"""Optimistic locking tests for TaskExecution aggregate."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


_NOW = datetime(2024, 1, 1, 12, 0, 0)


class TestTaskExecutionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        uow1 = SqlAlchemyUnitOfWork(session_factory)
        uow2 = SqlAlchemyUnitOfWork(session_factory)

        async with uow1 as u:
            task = TaskExecution.create(
                id_=TaskExecutionId.generate(),
                name="optimistic-test",
                now=_NOW,
            )
            await u.task_execution_repository.save(task)
            await u.commit()
            task_id = task.id

        async with uow1 as u1:
            entity_a = await u1.task_execution_repository.get_by_id(task_id)
            assert entity_a is not None

            async with uow2 as u2:
                entity_b = await u2.task_execution_repository.get_by_id(task_id)
                assert entity_b is not None

                entity_a.start(now=_NOW)
                await u1.task_execution_repository.save(entity_a)
                await u1.commit()

                entity_b.start(now=_NOW)
                await u2.task_execution_repository.save(entity_b)
                with pytest.raises(ConcurrentModificationError):
                    await u2.commit()
