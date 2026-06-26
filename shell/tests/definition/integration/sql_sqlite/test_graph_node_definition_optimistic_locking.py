"""Optimistic locking tests for GraphNodeDefinition entity."""

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
from shell.infrastructure.definition.persistence.sql.repositories.sql_graph_node_definition_repository import (
    SqlGraphNodeDefinitionRepository,
)
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestGraphNodeDefinitionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        uow1 = SqlAlchemyUnitOfWork(session_factory)
        uow2 = SqlAlchemyUnitOfWork(session_factory)
        gd_id = GraphDefinitionId.generate()
        nd_id = GraphNodeDefinitionId.generate()

        async with uow1 as u:
            graph_def = GraphDefinition(id=gd_id, name="test", purpose="test")
            await u.graph_definition_repository.save(graph_def)

            node = GraphNodeDefinition(
                id=nd_id,
                position=0,
                mode=Mode("agent"),
                role="agent",
                node_type="agent",
            )
            repo = SqlGraphNodeDefinitionRepository(u._active_session)
            await repo.save(node, gd_id)
            await u.commit()

        async with uow1 as u1:
            repo1 = SqlGraphNodeDefinitionRepository(u1._active_session)
            entity_a = await repo1.get_by_id(nd_id)
            assert entity_a is not None

            async with uow2 as u2:
                repo2 = SqlGraphNodeDefinitionRepository(u2._active_session)
                entity_b = await repo2.get_by_id(nd_id)
                assert entity_b is not None

                modified_a = GraphNodeDefinition(
                    id=nd_id,
                    position=1,
                    mode=Mode("agent"),
                    role="agent",
                    node_type="agent",
                )
                await repo1.save(modified_a, gd_id)
                await u1.commit()

                modified_b = GraphNodeDefinition(
                    id=nd_id,
                    position=2,
                    mode=Mode("agent"),
                    role="agent",
                    node_type="agent",
                )
                await repo2.save(modified_b, gd_id)
                with pytest.raises(ConcurrentModificationError):
                    await u2.commit()
