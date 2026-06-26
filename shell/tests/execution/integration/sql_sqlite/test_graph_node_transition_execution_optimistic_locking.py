"""Optimistic locking tests for GraphNodeTransitionExecution aggregate."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_node_transition_execution.graph_node_transition_execution import (
    GraphNodeTransitionExecution,
)
from shell.domain.execution.aggregates.graph_node_transition_execution.value_objects.graph_node_transition_execution_id import (
    GraphNodeTransitionExecutionId,
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


class TestGraphNodeTransitionExecutionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        uow1 = SqlAlchemyUnitOfWork(session_factory)
        uow2 = SqlAlchemyUnitOfWork(session_factory)

        ge_id = GraphExecutionId.generate()
        src_id = GraphNodeExecutionId.generate()
        tgt_id = GraphNodeExecutionId.generate()

        async with uow1 as u:
            transition = GraphNodeTransitionExecution.create_sequence(
                id_=GraphNodeTransitionExecutionId.generate(),
                graph_execution_id=ge_id,
                source_node_execution_id=src_id,
                target_node_execution_id=tgt_id,
            )
            await u.graph_node_transition_execution_repository.save(transition)
            await u.commit()
            tx_id = transition.id

        async with uow1 as u1:
            entity_a = await u1.graph_node_transition_execution_repository.get_by_id(tx_id)
            assert entity_a is not None

            async with uow2 as u2:
                entity_b = await u2.graph_node_transition_execution_repository.get_by_id(tx_id)
                assert entity_b is not None

                entity_a.take(now=_NOW)
                await u1.graph_node_transition_execution_repository.save(entity_a)
                await u1.commit()

                entity_b.take(now=_NOW)
                await u2.graph_node_transition_execution_repository.save(entity_b)
                with pytest.raises(ConcurrentModificationError):
                    await u2.commit()
