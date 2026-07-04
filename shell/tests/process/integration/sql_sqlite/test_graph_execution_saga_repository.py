"""SQLite integration tests for GraphExecutionSaga repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.execution.persistence.sql.repositories.sql_graph_execution_saga_repository import (
    SqlGraphExecutionSagaRepository,
)
from shell.process.execution.graph_execution_saga.state import (
    GraphExecutionSagaState,
    GraphExecutionSagaStatus,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestGraphExecutionSagaRepositorySqlite:
    async def test_save_and_get_by_graph_execution_id(
        self, session_factory: async_sessionmaker
    ) -> None:
        async with session_factory() as session:
            repo = SqlGraphExecutionSagaRepository(session)
            saga = GraphExecutionSagaState(
                saga_id="saga-sql-1",
                graph_execution_id="ge-sql-1",
                expected_nodes_count=3,
            )
            await repo.save(saga)
            await session.commit()

        async with session_factory() as session:
            repo = SqlGraphExecutionSagaRepository(session)
            stored = await repo.get_by_graph_execution_id("ge-sql-1")

            assert stored is not None
            assert stored.saga_id == "saga-sql-1"
            assert stored.graph_execution_id == "ge-sql-1"
            assert stored.expected_nodes_count == 3
            assert stored.status == GraphExecutionSagaStatus.PENDING
            assert stored.version == 1

    async def test_update_existing_saga(self, session_factory: async_sessionmaker) -> None:
        async with session_factory() as session:
            repo = SqlGraphExecutionSagaRepository(session)
            saga = GraphExecutionSagaState(
                saga_id="saga-sql-2",
                graph_execution_id="ge-sql-2",
                expected_nodes_count=2,
            )
            await repo.save(saga)
            await session.commit()

        async with session_factory() as session:
            repo = SqlGraphExecutionSagaRepository(session)
            stored = await repo.get_by_graph_execution_id("ge-sql-2")
            assert stored is not None
            stored.record_node_execution_created("ndef-1", "nexec-1")
            stored.record_node_execution_created("ndef-2", "nexec-2")
            await repo.save(stored)
            await session.commit()

        async with session_factory() as session:
            repo = SqlGraphExecutionSagaRepository(session)
            stored = await repo.get_by_graph_execution_id("ge-sql-2")
            assert stored is not None
            assert stored.status == GraphExecutionSagaStatus.COMPLETED
            assert stored.version > 1

    async def test_get_nonexistent_returns_none(self, session_factory: async_sessionmaker) -> None:
        async with session_factory() as session:
            repo = SqlGraphExecutionSagaRepository(session)
            result = await repo.get_by_graph_execution_id("nonexistent")
            assert result is None

    async def test_unique_graph_execution_id_enforced(
        self, session_factory: async_sessionmaker
    ) -> None:
        async with session_factory() as session:
            repo = SqlGraphExecutionSagaRepository(session)
            saga_1 = GraphExecutionSagaState(
                saga_id="saga-sql-3a",
                graph_execution_id="ge-sql-3",
                expected_nodes_count=1,
            )
            await repo.save(saga_1)
            await session.commit()

        async with session_factory() as session:
            repo = SqlGraphExecutionSagaRepository(session)
            saga_2 = GraphExecutionSagaState(
                saga_id="saga-sql-3b",
                graph_execution_id="ge-sql-3",
                expected_nodes_count=5,
            )
            with pytest.raises(IntegrityError):
                await repo.save(saga_2)
                await session.commit()

    async def test_persists_node_definition_executions(
        self, session_factory: async_sessionmaker
    ) -> None:
        async with session_factory() as session:
            repo = SqlGraphExecutionSagaRepository(session)
            saga = GraphExecutionSagaState(
                saga_id="saga-sql-4",
                graph_execution_id="ge-sql-4",
                expected_nodes_count=3,
            )
            saga.record_node_execution_created("ndef-a", "nexec-a")
            saga.record_node_execution_created("ndef-b", "nexec-b")
            await repo.save(saga)
            await session.commit()

        async with session_factory() as session:
            repo = SqlGraphExecutionSagaRepository(session)
            stored = await repo.get_by_graph_execution_id("ge-sql-4")
            assert stored is not None
            assert stored.node_definition_executions == {
                "ndef-a": "nexec-a",
                "ndef-b": "nexec-b",
            }
