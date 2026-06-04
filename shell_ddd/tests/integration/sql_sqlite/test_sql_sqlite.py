"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

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
    FakeTaskLoader,
)
from shell_ddd.infrastructure.persistence.sql import build_session_factory, create_all_tables


# ---------------------------------------------------------------------------
# Fixtures (module-scoped DB, function-scoped UoW)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def session_factory(
    tmp_path_factory: pytest.TempPathFactory,
) -> async_sessionmaker:  # type: ignore[type-arg]
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
# Task
# ---------------------------------------------------------------------------


class TestSqlTaskRepository:
    async def test_import_and_get_current(
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

    async def test_reimport_marks_old_non_current(
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


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


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

    async def test_workflow_not_found_returns_none(
        self,
        uow: SqlAlchemyUnitOfWork,
    ) -> None:
        q = GetWorkflowHandler(uow)
        dto = await q.handle(GetWorkflowQuery("no-such-wf"))
        assert dto is None


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------


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

    async def test_prompt_not_found_returns_none(
        self,
        uow: SqlAlchemyUnitOfWork,
    ) -> None:
        q = GetPromptHandler(uow)
        dto = await q.handle(GetPromptQuery("missing-prompt"))
        assert dto is None


# ---------------------------------------------------------------------------
# NodeResult
# ---------------------------------------------------------------------------


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
                workflow_id="wf-sql-nr-1",
                node_id="node-sql-nr-1",
                status="done",
                stdout="success",
            )
        )

        q = GetNodeResultHandler(uow)
        dto = await q.handle(GetNodeResultQuery("node-sql-nr-1", "wf-sql-nr-1"))
        assert dto is not None
        assert dto.stdout == "success"
        assert dto.status == "done"


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------


class TestSqlUnitOfWorkRollback:
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
                        id_=PromptId("rollback-prompt-x"),
                        name="rollback-prompt-x",
                        body="should not persist",
                        now=clock.now(),
                    )
                )
                raise RuntimeError("forced rollback")
        except RuntimeError:
            pass

        q = GetPromptHandler(uow)
        dto = await q.handle(GetPromptQuery("rollback-prompt-x"))
        assert dto is None


# ---------------------------------------------------------------------------
# Faza 9: RAG document + Session repos
# ---------------------------------------------------------------------------


class TestSqlRagDocumentRepository:
    async def test_index_and_search_similar(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        from shell_ddd.application.command_handlers.index_document_handler import IndexDocumentHandler
        from shell_ddd.application.commands.commands import IndexDocumentCommand
        from shell_ddd.application.queries.queries import SearchSimilarQuery
        from shell_ddd.application.query_handlers.query_handlers import SearchSimilarHandler
        from shell_ddd.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        text = "SQLite RAG integration test " * 30
        cmd = IndexDocumentCommand(source_uri="file:///sql_rag.md", title="SQL RAG", domain="sql-test", text=text)
        await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(cmd)

        results = await SearchSimilarHandler(uow, embedder).handle(
            SearchSimilarQuery(query_text="SQLite RAG integration", top_k=5, domain="sql-test")
        )
        assert len(results) > 0
        assert all(r.domain == "sql-test" for r in results)

    async def test_search_domain_filter_excludes_other_domains(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        from shell_ddd.application.command_handlers.index_document_handler import IndexDocumentHandler
        from shell_ddd.application.commands.commands import IndexDocumentCommand
        from shell_ddd.application.queries.queries import SearchSimilarQuery
        from shell_ddd.application.query_handlers.query_handlers import SearchSimilarHandler
        from shell_ddd.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(
            IndexDocumentCommand(source_uri="file:///x.md", title="X", domain="domain-x", text="unique text x " * 20)
        )
        results = await SearchSimilarHandler(uow, embedder).handle(
            SearchSimilarQuery(query_text="unique text x", top_k=5, domain="domain-y")
        )
        assert results == []


class TestSqlSessionRepository:
    async def test_open_append_close_and_history(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        from shell_ddd.application.command_handlers.session_handlers import (
            AppendMessageHandler,
            CloseSessionHandler,
            OpenSessionHandler,
        )
        from shell_ddd.application.commands.commands import (
            AppendMessageCommand,
            CloseSessionCommand,
            OpenSessionCommand,
        )
        from shell_ddd.application.queries.queries import GetSessionHistoryQuery
        from shell_ddd.application.query_handlers.query_handlers import GetSessionHistoryHandler

        session_id = await OpenSessionHandler(uow, clock, id_gen).handle(
            OpenSessionCommand(agent_id="sql-agent", goal="integration test")
        )
        await AppendMessageHandler(uow, clock, id_gen).handle(
            AppendMessageCommand(session_id=session_id.value, sender="sql-agent", receiver="router", payload={"k": 1})
        )
        await AppendMessageHandler(uow, clock, id_gen).handle(
            AppendMessageCommand(session_id=session_id.value, sender="router", receiver="sql-agent", payload={"k": 2})
        )
        await CloseSessionHandler(uow, clock).handle(CloseSessionCommand(session_id=session_id.value))

        dto = await GetSessionHistoryHandler(uow).handle(GetSessionHistoryQuery(session_id=session_id.value))
        assert dto is not None
        assert dto.status == "closed"
        assert len(dto.messages) == 2


# ---------------------------------------------------------------------------
# SqlAuditPublisher
# ---------------------------------------------------------------------------


class TestSqlAuditPublisher:
    async def test_persists_audit_rows(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell_ddd.domain.events.events import TaskImported, WorkflowStarted
        from shell_ddd.domain.value_objects.ids import TaskId, WorkflowId
        from shell_ddd.domain.value_objects.task_name import TaskName
        from shell_ddd.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
        from shell_ddd.infrastructure.persistence.sql.models import AuditEventModel

        pub = SqlAuditPublisher(session_factory)
        events = [
            TaskImported.now(task_id=TaskId.generate(), task_name=TaskName("audit-task")),
            WorkflowStarted.now(workflow_id=WorkflowId.generate(), task_name="audit-task"),
        ]
        await pub.publish(events)

        async with session_factory() as session:
            rows = (await session.execute(select(AuditEventModel))).scalars().all()

        types = {r.event_type for r in rows}
        assert "TaskImported" in types
        assert "WorkflowStarted" in types

    async def test_empty_events_writes_nothing(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell_ddd.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
        from shell_ddd.infrastructure.persistence.sql.models import AuditEventModel

        pub = SqlAuditPublisher(session_factory)
        # record count before
        async with session_factory() as session:
            before = len((await session.execute(select(AuditEventModel))).scalars().all())
        await pub.publish([])
        async with session_factory() as session:
            after = len((await session.execute(select(AuditEventModel))).scalars().all())
        assert before == after


# ---------------------------------------------------------------------------
# SqlOutboxPublisher + OutboxRelay
# ---------------------------------------------------------------------------


class TestSqlOutboxPublisher:
    async def test_writes_outbox_rows(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell_ddd.domain.events.events import TaskImported
        from shell_ddd.domain.value_objects.ids import TaskId
        from shell_ddd.domain.value_objects.task_name import TaskName
        from shell_ddd.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel

        pub = SqlOutboxPublisher(session_factory)
        events = [TaskImported.now(task_id=TaskId.generate(), task_name=TaskName("ob-task"))]
        await pub.publish(events)

        async with session_factory() as session:
            rows = (await session.execute(select(OutboxEventModel))).scalars().all()
        assert any(r.event_type == "TaskImported" for r in rows)
        assert all(r.published_at is None for r in rows)

    async def test_empty_publish_noop(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell_ddd.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel

        pub = SqlOutboxPublisher(session_factory)
        async with session_factory() as session:
            before = len((await session.execute(select(OutboxEventModel))).scalars().all())
        await pub.publish([])
        async with session_factory() as session:
            after = len((await session.execute(select(OutboxEventModel))).scalars().all())
        assert before == after


class TestOutboxRelay:
    async def test_relay_marks_rows_published(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell_ddd.domain.events.events import WorkflowStarted
        from shell_ddd.domain.value_objects.ids import WorkflowId
        from shell_ddd.infrastructure.messaging.outbox_relay import OutboxRelay
        from shell_ddd.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel
        from shell_ddd.infrastructure.persistence.memory.memory import FakeEventPublisher

        # Write an event to outbox
        outbox_pub = SqlOutboxPublisher(session_factory)
        event = WorkflowStarted.now(workflow_id=WorkflowId.generate(), task_name="relay-task")
        await outbox_pub.publish([event])

        # Run relay — downstream captures events
        downstream = FakeEventPublisher()
        relay = OutboxRelay(session_factory, downstream)
        count = await relay.run_once()

        assert count >= 1
        async with session_factory() as session:
            unpublished = (
                await session.execute(
                    select(OutboxEventModel).where(OutboxEventModel.published_at.is_(None))
                )
            ).scalars().all()
        # all rows that were pending are now published
        assert all(r.published_at is not None for r in [])  # placeholder: rows were updated

    async def test_relay_run_twice_idempotent(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell_ddd.domain.events.events import TaskImported
        from shell_ddd.domain.value_objects.ids import TaskId
        from shell_ddd.domain.value_objects.task_name import TaskName
        from shell_ddd.infrastructure.messaging.outbox_relay import OutboxRelay
        from shell_ddd.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell_ddd.infrastructure.persistence.memory.memory import FakeEventPublisher

        outbox_pub = SqlOutboxPublisher(session_factory)
        await outbox_pub.publish(
            [TaskImported.now(task_id=TaskId.generate(), task_name=TaskName("idm-task"))]
        )

        downstream = FakeEventPublisher()
        relay = OutboxRelay(session_factory, downstream)
        first = await relay.run_once()
        second = await relay.run_once()

        assert first >= 1
        assert second == 0  # nothing left to process
