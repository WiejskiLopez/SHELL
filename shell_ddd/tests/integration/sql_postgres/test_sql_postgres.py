"""PostgreSQL integration tests — mirrors sql_sqlite tests on a real Postgres instance.

Skip all tests when PG_TEST_URL is not set:
    export PG_TEST_URL=postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test

Start Postgres via docker-compose:
    docker compose -f shell_ddd/docker-compose.test.yml up -d postgres
"""
from __future__ import annotations

import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from shell_ddd.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell_ddd.infrastructure.persistence.sql.query_services import SqlQueryServices

from shell_ddd.application.command_handlers.import_task_handler import ImportTaskHandler
from shell_ddd.application.command_handlers.save_node_result_handler import SaveNodeResultHandler
from shell_ddd.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell_ddd.application.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell_ddd.application.commands.commands import (
    ImportTaskCommand,
    SaveNodeResultCommand,
    SavePromptCommand,
    StartWorkflowCommand,
)
from shell_ddd.application.queries.queries import (
    GetCurrentTaskQuery,
    GetNodeResultQuery,
    GetPromptQuery,
    GetWorkflowQuery,
)
from shell_ddd.application.query_handlers.query_handlers import (
    GetCurrentTaskHandler,
    GetNodeResultHandler,
    GetPromptHandler,
    GetWorkflowHandler,
)
from shell_ddd.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell_ddd.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
)
from shell_ddd.infrastructure.persistence.sql import build_session_factory

_PG_URL = os.environ.get(
    "PG_TEST_URL", "postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test"
)

pytestmark = pytest.mark.skipif(
    os.environ.get("PG_TEST_URL") is None,
    reason="PG_TEST_URL not set — start Postgres via docker-compose and set PG_TEST_URL",
)


# ---------------------------------------------------------------------------
# Fixtures (module-scoped DB with fresh schema, function-scoped UoW)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def session_factory() -> async_sessionmaker:  # type: ignore[type-arg]
    #await create_all_tables(_PG_URL)
    await bootstrap_database(_PG_URL)
    return build_session_factory(_PG_URL)


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def uow(
    session_factory: async_sessionmaker,  # type: ignore[type-arg]
    events: FakeEventPublisher,
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory, post_commit_publisher=events)


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture()
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def task_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# PG Task")


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class TestPgTaskRepository:
    async def test_import_and_get_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, FakeLogger())
        await handler.handle(ImportTaskCommand("t.md", "pg-task"))

        q = GetCurrentTaskHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskQuery("pg-task"))
        assert dto is not None
        assert dto.name == "pg-task"
        assert dto.is_current is True

    async def test_reimport_marks_old_non_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, FakeLogger())
        await handler.handle(ImportTaskCommand("t.md", "pg-task-v"))
        await handler.handle(ImportTaskCommand("t.md", "pg-task-v"))

        q = GetCurrentTaskHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskQuery("pg-task-v"))
        assert dto is not None
        assert dto.is_current is True


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


class TestPgWorkflowRepository:
    async def test_start_and_query_workflow(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_loader: FakeTaskLoader,
    ) -> None:
        imp = ImportTaskHandler(uow, clock, id_gen, task_loader, FakeLogger())
        await imp.handle(ImportTaskCommand("t.md", "pg-wf-task"))

        start = StartWorkflowHandler(uow, clock, id_gen)
        wf_id = await start.handle(StartWorkflowCommand("pg-wf-task"))

        q = GetWorkflowHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"
        assert dto.task_name == "pg-wf-task"

    async def test_workflow_not_found_returns_none(
        self,
        uow: SqlAlchemyUnitOfWork,
    ) -> None:
        q = GetWorkflowHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetWorkflowQuery("pg-no-such-wf"))
        assert dto is None


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------


class TestPgPromptRepository:
    async def test_save_and_get_prompt(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("pg-sys-prompt", "You are a pg helper."))

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("pg-sys-prompt"))
        assert dto is not None
        assert dto.body == "You are a pg helper."

    async def test_prompt_not_found_returns_none(
        self,
        uow: SqlAlchemyUnitOfWork,
    ) -> None:
        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("pg-missing-prompt"))
        assert dto is None


# ---------------------------------------------------------------------------
# NodeResult
# ---------------------------------------------------------------------------


class TestPgNodeResultRepository:
    async def test_save_and_get_result(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
    ) -> None:
        handler = SaveNodeResultHandler(uow, clock, id_gen)
        await handler.handle(
            SaveNodeResultCommand(
                workflow_id="pg-wf-nr-1",
                node_id="pg-node-nr-1",
                status="done",
                stdout="pg success",
            )
        )

        q = GetNodeResultHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetNodeResultQuery("pg-node-nr-1", "pg-wf-nr-1"))
        assert dto is not None
        assert dto.stdout == "pg success"
        assert dto.status == "done"


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------


class TestPgUnitOfWorkRollback:
    async def test_rollback_on_exception_leaves_db_clean(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        try:
            async with uow as u:
                from shell_ddd.domain.entities.prompt import Prompt
                from shell_ddd.domain.value_objects.ids import PromptId

                await u.prompts.save(
                    Prompt.new(
                        id_=PromptId("pg-rollback-prompt-x"),
                        name="pg-rollback-prompt-x",
                        body="should not persist",
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced pg rollback")
        except RuntimeError:
            pass

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("pg-rollback-prompt-x"))
        assert dto is None
