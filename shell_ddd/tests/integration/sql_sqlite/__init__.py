"""SQLite integration test package."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.entities.prompt import Prompt
from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.value_objects.ids import (
    NodeId,
    NodeResultId,
    PromptId,
    TaskId,
    WorkflowId,
)
from shell_ddd.domain.value_objects.status import Status
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell_ddd.infrastructure.persistence.memory.memory import FakeClock
from shell_ddd.infrastructure.persistence.sql import build_session_factory, create_all_tables


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def session_factory(tmp_path_factory: pytest.TempPathFactory) -> async_sessionmaker:  # type: ignore[type-arg]
    db = tmp_path_factory.mktemp("sqlite") / "test.db"
    url = f"sqlite+aiosqlite:///{db}"
    await create_all_tables(url)
    return build_session_factory(url)


@pytest.fixture()
def uow(session_factory: async_sessionmaker) -> SqlAlchemyUnitOfWork:  # type: ignore[type-arg]
    return SqlAlchemyUnitOfWork(session_factory)


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


# ---------------------------------------------------------------------------
# Task repository
# ---------------------------------------------------------------------------


class TestSqlTaskRepository:
    async def test_save_and_get_by_id(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        task = Task.new(
            id_=TaskId("task-sql-1"),
            name=TaskName("sql-task"),
            body_md="# hello",
            body_yaml_raw="graph: []",
            now=clock.now(),
        )
        async with uow as u:
            await u.tasks.save(task)
            await u.commit()

        async with uow as u:
            result = await u.tasks.get_by_id(TaskId("task-sql-1"))
        assert result is not None
        assert result.name == TaskName("sql-task")
        assert result.is_current is True

    async def test_get_nonexistent_returns_none(
        self, uow: SqlAlchemyUnitOfWork
    ) -> None:
        async with uow as u:
            result = await u.tasks.get_by_id(TaskId("nonexistent"))
        assert result is None

    async def test_get_current_by_name(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        task = Task.new(
            id_=TaskId("task-sql-2"),
            name=TaskName("current-task"),
            body_md="# current",
            body_yaml_raw="graph: []",
            now=clock.now(),
        )
        async with uow as u:
            await u.tasks.save(task)
            await u.commit()

        async with uow as u:
            result = await u.tasks.get_current_by_name(TaskName("current-task"))
        assert result is not None
        assert result.id == TaskId("task-sql-2")


# ---------------------------------------------------------------------------
# Workflow repository
# ---------------------------------------------------------------------------


class TestSqlWorkflowRepository:
    async def test_save_and_get_workflow(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        wf = Workflow.new(
            id_=WorkflowId("wf-sql-1"),
            task_name="wf-task",
            now=clock.now(),
        )
        async with uow as u:
            await u.workflows.save(wf)
            await u.commit()

        async with uow as u:
            result = await u.workflows.get_by_id(WorkflowId("wf-sql-1"))
        assert result is not None
        assert result.task_name == "wf-task"

    async def test_workflow_not_found_returns_none(
        self, uow: SqlAlchemyUnitOfWork
    ) -> None:
        async with uow as u:
            result = await u.workflows.get_by_id(WorkflowId("no-such-wf"))
        assert result is None


# ---------------------------------------------------------------------------
# Prompt repository
# ---------------------------------------------------------------------------


class TestSqlPromptRepository:
    async def test_save_and_get_prompt(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        prompt = Prompt.new(
            id_=PromptId("prompt-sql-1"),
            name="sys-prompt",
            body="You are helpful.",
            now=clock.now(),
        )
        async with uow as u:
            await u.prompts.save(prompt)
            await u.commit()

        async with uow as u:
            result = await u.prompts.get_current_by_name("sys-prompt")
        assert result is not None
        assert result.body == "You are helpful."

    async def test_prompt_not_found_returns_none(
        self, uow: SqlAlchemyUnitOfWork
    ) -> None:
        async with uow as u:
            result = await u.prompts.get_current_by_name("missing-prompt")
        assert result is None


# ---------------------------------------------------------------------------
# NodeResult repository
# ---------------------------------------------------------------------------


class TestSqlNodeResultRepository:
    async def test_save_and_get_node_result(
        self, uow: SqlAlchemyUnitOfWork, clock: FakeClock
    ) -> None:
        result_entity = NodeResult.new(
            id_=NodeResultId("nr-sql-1"),
            node_id=NodeId("node-1"),
            workflow_id=WorkflowId("wf-nr-1"),
            status=Status.done(),
            stdout="output",
            stderr="",
            now=clock.now(),
        )
        async with uow as u:
            await u.node_results.save(result_entity)
            await u.commit()

        async with uow as u:
            found = await u.node_results.get_by_node_and_workflow(
                NodeId("node-1"), WorkflowId("wf-nr-1")
            )
        assert found is not None
        assert found.status == Status.done()
        assert found.stdout == "output"


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
def clock() -> FakeClock:
    return FakeClock()


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
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await handler.handle(ImportTaskCommand("t.md", "t.yaml", "sql-task"))

        q = GetCurrentTaskHandler(uow)
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
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await handler.handle(ImportTaskCommand("t.md", "t.yaml", "sql-task-v"))
        await handler.handle(ImportTaskCommand("t.md", "t.yaml", "sql-task-v"))

        q = GetCurrentTaskHandler(uow)
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
    ) -> None:
        imp = ImportTaskHandler(uow, clock, id_gen, task_loader, events)
        await imp.handle(ImportTaskCommand("t.md", "t.yaml", "wf-task"))

        start = StartWorkflowHandler(uow, clock, id_gen, events)
        wf_id = await start.handle(StartWorkflowCommand("wf-task"))

        q = GetWorkflowHandler(uow)
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
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("sys-prompt", "You are helpful."))

        q = GetPromptHandler(uow)
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

        q = GetNodeResultHandler(uow)
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
                    __import__(
                        "shell_ddd.domain.entities.prompt", fromlist=["Prompt"]
                    ).Prompt.new(
                        id_=id_gen.new_prompt_id(),
                        name="rollback-prompt",
                        body="body",
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        uow2 = SqlAlchemyUnitOfWork(session_factory)
        q = GetPromptHandler(uow2)
        dto = await q.handle(GetPromptQuery("rollback-prompt"))
        assert dto is None
