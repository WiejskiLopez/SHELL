"""SQLite integration test package."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.application.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.command_handlers.save_graph_node_execution_result_handler import SaveGraphNodeExecutionResultHandler
from shell.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell.application.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell.application.commands.commands import (
    ImportTaskExecutionCommand,
    SaveGraphNodeExecutionResultCommand,
    SavePromptCommand,
    StartWorkflowCommand,
)
from shell.application.queries.queries import (
    GetCurrentTaskExecutionQuery,
    GetGraphNodeExecutionResultQuery,
    GetPromptQuery,
    GetWorkflowQuery,
)
from shell.application.query_handlers.query_handlers import (
    GetCurrentTaskExecutionHandler,
    GetGraphNodeExecutionResultHandler,
    GetPromptHandler,
    GetWorkflowHandler,
)
from shell.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell.domain.entities.graph_node_execution import GraphNodeExecution
from shell.domain.entities.prompt import Prompt
from shell.domain.value_objects.ids import (
    PromptId,
    TaskExecutionId,
)
from shell.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
)
from shell.infrastructure.persistence.sql import build_session_factory
from shell.infrastructure.persistence.sql.query_services import SqlQueryServices

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

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
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def uow(
    session_factory: async_sessionmaker,  # type: ignore[type-arg]
    events: FakeEventPublisher,
) -> SqlAlchemyUnitOfWork:
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
def task_execution_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# SQL Task")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSqlTaskExecutionRepository:
    async def test_save_and_get_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        handler = ImportTaskExecutionHandler(uow, clock, id_gen, task_execution_loader, FakeLogger())
        await handler.handle(ImportTaskExecutionCommand("t.md", "sql-task"))

        q = GetCurrentTaskExecutionHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskExecutionQuery("sql-task"))
        assert dto is not None
        assert dto.name == "sql-task"
        assert dto.is_current is True

    async def test_reimport_makes_old_non_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        handler = ImportTaskExecutionHandler(uow, clock, id_gen, task_execution_loader, FakeLogger())
        await handler.handle(ImportTaskExecutionCommand("t.md", "sql-task-v"))
        await handler.handle(ImportTaskExecutionCommand("t.md", "sql-task-v"))

        q = GetCurrentTaskExecutionHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskExecutionQuery("sql-task-v"))
        assert dto is not None
        assert dto.is_current is True


class TestSqlWorkflowRepository:
    async def test_start_and_query_workflow(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        imp = ImportTaskExecutionHandler(uow, clock, id_gen, task_execution_loader, FakeLogger())
        await imp.handle(ImportTaskExecutionCommand("t.md", "wf-task"))

        # Persist a single-node Graph so StartWorkflowHandler can anchor the cursor.
        from shell.domain.entities.graph_execution import GraphExecution, GraphNodeExecution
        from shell.domain.value_objects.ids import GraphDefinitionId, GraphExecutionId, GraphNodeExecutionId
        from shell.domain.value_objects.mode import Mode
        from shell.domain.value_objects.task_execution_name import TaskExecutionName

        async with uow as u:
            task_execution = await u.task_executions.get_current_by_name(TaskExecutionName("wf-task"))
            assert task_execution is not None

            # 1. Pobieramy prawdziwe ID przypisane do zaimportowanego zadania
            real_task_execution_id = task_execution.id.value

            graph_execution = GraphExecution(
                id=GraphExecutionId.generate(),
                task_execution_id=task_execution.id,
                graph_definition_id=GraphDefinitionId("tpl"),
                graph_node_executions=[
                    GraphNodeExecution(
                        id=GraphNodeExecutionId("wf-task-node-0"),
                        position=0,
                        node_dir="/fake/wf-task-0",
                        mode=Mode("agent"),
                        role="agent",
                        node_type="agent",
                    )
                ],
            )
            await u.graph_executions.save(graph_execution)
            await u.commit()

        start = StartWorkflowHandler(uow, clock, id_gen)
        # 2. Przekazujemy poprawne real_task_execution_id zamiast nazwy stringowej
        wf_id = await start.handle(StartWorkflowCommand(real_task_execution_id))

        q = GetWorkflowHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"
        # 3. Sprawdzamy identyfikator zadania w DTO zamiast nazwy tekstowej
        assert dto.task_execution_id == real_task_execution_id


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
        from shell.domain.entities.workflow import Workflow
        from shell.domain.value_objects.ids import WorkflowId

        async with uow as u:
            await u.workflows.save(
                Workflow.new(id_=WorkflowId("wf-sql-1"), task_execution_id=TaskExecutionId("task-id"), now=clock.now())
            )
            await u.commit()

        handler = SaveGraphNodeExecutionResultHandler(uow, clock, id_gen)
        await handler.handle(
            SaveGraphNodeExecutionResultCommand(
                workflow_id="wf-sql-1",
                graph_node_execution_id="node-sql-1",
                status="done",
                stdout="success",
            )
        )

        q = GetGraphNodeExecutionResultHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetGraphNodeExecutionResultQuery("node-sql-1", "wf-sql-1"))
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
