"""Optimistic locking tests for GraphExecution aggregate."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from shell.domain.execution.aggregates.graph_execution.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
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


class TestGraphExecutionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        uow1 = SqlAlchemyUnitOfWork(session_factory)
        uow2 = SqlAlchemyUnitOfWork(session_factory)

        te_id = TaskExecutionId.generate()

        async with uow1 as u:
            graph = GraphExecution.create_main_round(
                id_=GraphExecutionId.generate(),
                task_execution_id=te_id,
            )
            await u.graph_execution_repository.save(graph)
            await u.commit()
            graph_id = graph.id

        async with uow1 as u1:
            entity_a = await u1.graph_execution_repository.get_by_id(graph_id)
            assert entity_a is not None

            async with uow2 as u2:
                entity_b = await u2.graph_execution_repository.get_by_id(graph_id)
                assert entity_b is not None

                entity_a.start_planning(now=_NOW)
                await u1.graph_execution_repository.save(entity_a)
                await u1.commit()

                entity_b.start_planning(now=_NOW)
                await u2.graph_execution_repository.save(entity_b)
                with pytest.raises(ConcurrentModificationError):
                    await u2.commit()
