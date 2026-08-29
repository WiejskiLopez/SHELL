"""Kontrakt repozytorium graph_execution — deterministyczna kolejność wyników.

Adapter SQL i in-memory muszą zwracać tę samą kolejność dla lookups po
task_execution_id / parent_id, dzięki czemu selekcja ``result[0]`` jest
deterministyczna i stabilna między SQLite a PostgreSQL.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.graph_execution.graph_execution import (
    GraphExecution,
)
from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_definition_id_ref import (
    GraphDefinitionIdRef,
)
from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_execution_status import (
    GraphExecutionStatus,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.execution_service.infrastructure.execution.graph_execution.persistence.sql.models.graph_execution import (
    GraphExecutionModel,
)
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
        GraphExecutionRepository,
    )

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_TASK = TaskExecutionId("task-deterministic")


def _now(seconds: int) -> datetime:
    return datetime(2026, 1, 1, 0, 0, seconds, tzinfo=UTC)


def _entity(graph_id: str, seconds: int) -> GraphExecution:
    return GraphExecution.initialize(
        id_=GraphExecutionId(graph_id),
        task_execution_id=_TASK,
        graph_definition_id=GraphDefinitionIdRef("def-1"),
        now=OccurredAt.from_datetime(_now(seconds)),
    )


def _db_row(graph_id: str, seconds: int) -> GraphExecutionModel:
    row = GraphExecutionModel(
        id=graph_id,
        task_execution_id=_TASK.value,
        graph_definition_id="def-1",
        status=GraphExecutionStatus.PENDING.value,
        created_at=_now(seconds),
    )
    return row


async def _clean_sql(session_factory: async_sessionmaker) -> None:
    from sqlalchemy import delete

    async with session_factory() as session:
        await session.execute(
            delete(GraphExecutionModel).where(GraphExecutionModel.task_execution_id == _TASK.value)
        )
        await session.commit()


class TestMemoryGraphExecutionOrdering:
    async def test_get_by_task_execution_id_orders_by_created_at(self) -> None:
        from shell.execution_service.infrastructure.execution.graph_execution.persistence.memory.in_memory_graph_execution_repository import (
            InMemoryGraphExecutionRepository,
        )

        repository: GraphExecutionRepository = InMemoryGraphExecutionRepository()
        await repository.save(_entity("g2", seconds=2))
        await repository.save(_entity("g1", seconds=1))
        await repository.save(_entity("g3", seconds=3))

        result = await repository.get_by_task_execution_id(_TASK)
        assert [graph_execution.id.value for graph_execution in result] == ["g1", "g2", "g3"]


class TestSqlGraphExecutionOrdering:
    async def test_get_by_task_execution_id_orders_by_created_at(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.execution_service.infrastructure.execution.graph_execution.persistence.sql.repositories.sql_graph_execution_repository import (
            SqlGraphExecutionRepository,
        )

        await _clean_sql(session_factory)
        async with session_factory() as session:
            session.add(_db_row("g2", seconds=2))
            session.add(_db_row("g1", seconds=1))
            session.add(_db_row("g3", seconds=3))
            await session.commit()

        async with session_factory() as session:
            repository = SqlGraphExecutionRepository(session)
            result = await repository.get_by_task_execution_id(_TASK)
        assert [graph_execution.id.value for graph_execution in result] == ["g1", "g2", "g3"]
