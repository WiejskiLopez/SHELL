"""Optimistic locking tests for GraphDefinition entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from shell.domain.definition.entities.graph_definition import GraphDefinition
from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
from shell.domain.definition.value_objects.ids import (
    GraphDefinitionId,
    GraphNodeDefinitionId,
)
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestGraphDefinitionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        uow1 = SqlAlchemyUnitOfWork(session_factory)
        uow2 = SqlAlchemyUnitOfWork(session_factory)
        gd_id = GraphDefinitionId.generate()

        async with uow1 as u:
            entity = GraphDefinition(id=gd_id, name="v1", purpose="test")
            await u.graph_definition_repository.save(entity)
            await u.commit()

        async with uow1 as u1:
            await u1.graph_definition_repository.get(gd_id)

            async with uow2 as u2:
                await u2.graph_definition_repository.get(gd_id)

                modified_a = GraphDefinition(id=gd_id, name="v2", purpose="test")
                await u1.graph_definition_repository.save(modified_a)
                await u1.commit()

                modified_b = GraphDefinition(id=gd_id, name="v3", purpose="test")
                await u2.graph_definition_repository.save(modified_b)
                with pytest.raises(ConcurrentModificationError):
                    await u2.commit()
