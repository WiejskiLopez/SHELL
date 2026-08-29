"""Kontrakt repozytorium task_execution — deterministyczny lookup po nazwie.

Nazwa TaskExecution nie jest unikalna w bazie, więc ``get_by_name`` w obu
adapterach musi zwracać ten sam, deterministyczny rekord (najniższy ``id``) —
zamiast ``MultipleResultsFound`` (SQL) albo przypadkowego pierwszego rekordu
(in-memory).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import delete

from shell.execution_service.domain.execution.aggregates.task_execution.task_execution import (
    TaskExecution,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_name import (
    TaskExecutionName,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_name import (
    TaskName,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.work_dir import (
    WorkDir,
)
from shell.execution_service.domain.execution.aggregates.workflow.value_objects.workflow_id import (
    WorkflowId,
)
from shell.execution_service.infrastructure.execution.task_execution.persistence.sql.models.task_execution import (
    TaskExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.execution_service.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
        TaskExecutionRepository,
    )

_NAME_VALUE = "duplicate-name"
_NAME = TaskExecutionName("duplicate-name")
_WF = WorkflowId("wf-deterministic")
_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def _entity(task_id: str) -> TaskExecution:
    return TaskExecution.create(
        id_=TaskExecutionId(task_id),
        name=TaskName(_NAME_VALUE),
        now=CreatedAt.from_datetime(_NOW),
        workflow_id=_WF,
        work_dir=WorkDir("workdir/sample"),
    )


async def _clean_sql(session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        await session.execute(
            delete(TaskExecutionModel).where(TaskExecutionModel.workflow_id == _WF.value)
        )
        await session.commit()


class TestMemoryGetByNameDeterministic:
    async def test_duplicate_names_returns_lexicographically_first_id(self) -> None:
        from shell.execution_service.infrastructure.execution.task_execution.persistence.memory.in_memory_task_execution_repository import (
            InMemoryTaskExecutionRepository,
        )

        repository: TaskExecutionRepository = InMemoryTaskExecutionRepository()
        await repository.save(_entity("te-b"))
        await repository.save(_entity("te-a"))

        result = await repository.get_by_name(_NAME)
        assert result is not None
        assert result.id.value == "te-a"


class TestSqlGetByNameDeterministic:
    async def test_duplicate_names_returns_lexicographically_first_id(
        self,
        session_factory: async_sessionmaker,
    ) -> None:

        from shell.execution_service.infrastructure.execution.task_execution.persistence.sql.repositories.sql_task_execution_repository import (
            SqlTaskExecutionRepository,
        )

        await _clean_sql(session_factory)
        async with session_factory() as session:
            await _insert_task(session, "te-b")
            await _insert_task(session, "te-a")
            await session.commit()

        async with session_factory() as session:
            repository = SqlTaskExecutionRepository(session)
            result = await repository.get_by_name(_NAME)
        assert result is not None
        assert result.id.value == "te-a"


async def _insert_task(session: object, task_id: str) -> None:
    from sqlalchemy import insert

    typed = cast("AsyncSession", session)
    await typed.execute(
        insert(TaskExecutionModel).values(
            id=task_id,
            name=_NAME_VALUE,
            work_dir="workdir/sample",
            workflow_id=_WF.value,
            status="CREATED",
            created_at=_NOW,
        )
    )
