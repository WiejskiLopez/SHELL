"""Optimistic locking tests for GraphNodeExecution aggregate."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


_NOW = datetime(2024, 1, 1, 12, 0, 0)


class TestGraphNodeExecutionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        uow1 = SqlAlchemyUnitOfWork(session_factory)
        uow2 = SqlAlchemyUnitOfWork(session_factory)

        async with uow1 as u:
            node = GraphNodeExecution.new(
                id=GraphNodeExecutionId.generate(),
                position=0,
                mode="agent",
                role="agent",
                node_type="agent",
                now=_NOW,
            )
            await u.graph_node_execution_repository.save(node)
            await u.commit()
            node_id = node.id

        async with uow1 as u1:
            entity_a = await u1.graph_node_execution_repository.get_by_id(node_id)
            assert entity_a is not None

            async with uow2 as u2:
                entity_b = await u2.graph_node_execution_repository.get_by_id(node_id)
                assert entity_b is not None

                entity_a.start(now=_NOW)
                await u1.graph_node_execution_repository.save(entity_a)
                await u1.commit()

                entity_b.start(now=_NOW)
                await u2.graph_node_execution_repository.save(entity_b)
                with pytest.raises(ConcurrentModificationError):
                    await u2.commit()
