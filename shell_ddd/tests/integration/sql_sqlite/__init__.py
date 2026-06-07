"""SQLite integration test package."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from shell_ddd.application.command_handlers.import_task_handler import ImportTaskHandler
from shell_ddd.application.command_handlers.save_node_result_handler import SaveNodeResultHandler
from shell_ddd.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell_ddd.application.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell_ddd.application.commands.commands import ImportTaskCommand, StartWorkflowCommand, SaveNodeResultCommand, \
    SavePromptCommand
from shell_ddd.application.queries.queries import GetCurrentTaskQuery, GetWorkflowQuery, GetNodeResultQuery, \
    GetPromptQuery
from shell_ddd.application.query_handlers.query_handlers import GetCurrentTaskHandler, GetWorkflowHandler, \
    GetNodeResultHandler, GetPromptHandler
from shell_ddd.bootstrap.database_bootstrap import bootstrap_database

from shell_ddd.domain.entities.prompt import Prompt
from shell_ddd.domain.value_objects.ids import (
    PromptId,
)

from shell_ddd.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell_ddd.infrastructure.persistence.memory.memory import FakeClock, FakeTaskLoader, FakeEventPublisher, \
    FakeIdGenerator
from shell_ddd.infrastructure.persistence.sql import build_session_factory, create_all_tables
from shell_ddd.infrastructure.persistence.sql.query_services import SqlQueryServices


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def session_factory(tmp_path_factory: pytest.TempPathFactory) -> async_sessionmaker:  # type: ignore[type-arg]
    db = tmp_path_factory.mktemp("sqlite") / "test.db"
    url = f"sqlite+aiosqlite:///{db}"
    await bootstrap_database(url)
    return build_session_factory(url)


@pytest.fixture()
def uow(session_factory: async_sessionmaker) -> SqlAlchemyUnitOfWork:  # type: ignore[type-arg]
    return SqlAlchemyUnitOfWork(session_factory)


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


# ---------------------------------------------------------------------------
# UnitOfWork rollback
# ---------------------------------------------------------------------------


class TestSqlUnitOfWorkRollback:
    async def test_rollback_on_exception_leaves_db_clean(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        prompt = Prompt.new(
            id_=PromptId("rollback-prompt"),
            name="rollback-prompt",
            body="should not persist",
            now=clock.now(),
        )
        try:
            async with uow as u:
                await u.prompts.save(prompt)
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        async with uow as u:
            result = await u.prompts.get_current_by_name("rollback-prompt")
        assert result is None


@pytest.fixture()
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def task_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# SQL Task", yaml_raw="graph: []")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSqlTaskRepository:
    async def test_save_and_get_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await handler.handle(ImportTaskCommand("t.md", "sql-task"))

        q = GetCurrentTaskHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskQuery("sql-task"))
        assert dto is not None
        assert dto.name == "sql-task"
        assert dto.is_current is True

    async def test_reimport_makes_old_non_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await handler.handle(ImportTaskCommand("t.md", "sql-task-v"))
        await handler.handle(ImportTaskCommand("t.md", "sql-task-v"))

        q = GetCurrentTaskHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskQuery("sql-task-v"))
        assert dto is not None
        assert dto.is_current is True


class TestSqlWorkflowRepository:
    async def test_start_and_query_workflow(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        imp = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await imp.handle(ImportTaskCommand("t.md", "wf-task"))

        start = StartWorkflowHandler(uow, clock, id_gen, events)
        wf_id = await start.handle(StartWorkflowCommand("wf-task"))

        q = GetWorkflowHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"
        assert dto.task_name == "wf-task"


class TestSqlPromptRepository:
    async def test_save_and_get_prompt(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("sys-prompt", "You are helpful."))

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("sys-prompt"))
        assert dto is not None
        assert dto.body == "You are helpful."


class TestSqlNodeResultRepository:
    async def test_save_and_get_result(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        session_factory: async_sessionmaker,
    ) -> None:
        handler = SaveNodeResultHandler(uow, clock, id_gen, events)
        await handler.handle(
            SaveNodeResultCommand(
                workflow_id="wf-sql-1",
                node_id="node-sql-1",
                status="done",
                stdout="success",
            )
        )

        q = GetNodeResultHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetNodeResultQuery("node-sql-1", "wf-sql-1"))
        assert dto is not None
        assert dto.stdout == "success"
        assert dto.status == "done"


class TestSqlCommitRollback:
    async def test_rollback_on_exception(
        self,
        session_factory: async_sessionmaker,  # type: ignore[type-arg]
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        uow = SqlAlchemyUnitOfWork(session_factory)
        try:
            async with uow as u:
                await u.prompts.save(
                    Prompt.new(
                        id_=id_gen.new_prompt_id(),
                        name="rollback-prompt",
                        body="body",
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("rollback-prompt"))
        assert dto is None
