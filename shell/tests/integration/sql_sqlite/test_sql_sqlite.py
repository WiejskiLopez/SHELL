"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from shell.application.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.command_handlers.save_node_result_handler import SaveNodeResultHandler
from shell.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell.application.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell.application.commands.commands import (
    ImportTaskExecutionCommand,
    SaveNodeResultCommand,
    SavePromptCommand,
    StartWorkflowCommand,
)
from shell.application.queries.queries import (
    GetCurrentTaskExecutionQuery,
    GetNodeResultQuery,
    GetPromptQuery,
    GetWorkflowQuery,
)
from shell.application.query_handlers.query_handlers import (
    GetCurrentTaskExecutionHandler,
    GetNodeResultHandler,
    GetPromptHandler,
    GetWorkflowHandler,
)
from shell.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell.domain.events.events import WorkflowStarted
from shell.domain.value_objects.ids import TaskExecutionId, WorkflowId
from shell.infrastructure.logging.stdlib_logger import get_correlation_id
from shell.infrastructure.persistence import OutboxEventModel, SqlAlchemyUnitOfWork
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
# Fixtures (module-scoped DB, function-scoped UoW)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def session_factory(
    tmp_path_factory: pytest.TempPathFactory,
) -> async_sessionmaker:  # type: ignore[type-arg]
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


@pytest.fixture()
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def task_execution_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# SQL Task")


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class TestSqlTaskExecutionRepository:
    async def test_import_and_get_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory,
    ) -> None:
        handler = ImportTaskExecutionHandler(uow, clock, id_gen, task_execution_loader, FakeLogger())  # type: ignore[arg-type]
        await handler.handle(ImportTaskExecutionCommand("t.md", "sql-task"))

        q = GetCurrentTaskExecutionHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskExecutionQuery("sql-task"))
        assert dto is not None
        assert dto.name == "sql-task"
        assert dto.is_current is True

    async def test_reimport_marks_old_non_current(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory,
    ) -> None:
        handler = ImportTaskExecutionHandler(uow, clock, id_gen, task_execution_loader, FakeLogger())  # type: ignore[arg-type]
        await handler.handle(ImportTaskExecutionCommand("t.md", "sql-task-v"))
        await handler.handle(ImportTaskExecutionCommand("t.md", "sql-task-v"))

        q = GetCurrentTaskExecutionHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetCurrentTaskExecutionQuery("sql-task-v"))
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
        task_execution_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        imp = ImportTaskExecutionHandler(uow, clock, id_gen, task_execution_loader, FakeLogger())  # type: ignore[arg-type]
        await imp.handle(ImportTaskExecutionCommand("t.md", "wf-task"))

        # Persist a single-node Graph so StartWorkflowHandler can anchor the cursor.
        from shell.domain.entities.graph import Graph, GraphNode
        from shell.domain.value_objects.ids import GraphDefinitionId, GraphId, NodeId
        from shell.domain.value_objects.mode import Mode
        from shell.domain.value_objects.task_execution_name import TaskExecutionName

        async with uow as u:
            task_execution = await u.task_executions.get_current_by_name(TaskExecutionName("wf-task"))
            assert task_execution is not None

            # Pobieramy prawdziwe ID przypisane do zaimportowanego zadania
            real_task_execution_id = task_execution.id.value

            graph = Graph(
                id=GraphId.generate(),
                task_execution_id=task_execution.id,
                graph_definition_id=GraphDefinitionId("tpl"),
                nodes=[
                    GraphNode(
                        id=NodeId("wf-task-node-0"),
                        position=0,
                        node_dir="/fake/wf-task-0",
                        mode=Mode("agent"),
                        role="agent",
                        node_type="agent",
                    )
                ],
            )
            await u.graphs.save(graph)
            await u.commit()

        start = StartWorkflowHandler(uow, clock, id_gen)  # type: ignore[arg-type]
        # Przekazujemy poprawne real_task_execution_id zamiast nazwy stringowej
        wf_id = await start.handle(StartWorkflowCommand(real_task_execution_id))

        q = GetWorkflowHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"
        # POPRAWKA: Sprawdzamy identyfikator zadania zamiast nazwy tekstowej
        assert dto.task_execution_id == real_task_execution_id

    async def test_workflow_not_found_returns_none(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        q = GetWorkflowHandler(SqlQueryServices(session_factory))
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
        session_factory: async_sessionmaker,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)  # type: ignore[arg-type]
        await handler.handle(SavePromptCommand("sys-prompt", "You are helpful."))

        q = GetPromptHandler(SqlQueryServices(session_factory))
        dto = await q.handle(GetPromptQuery("sys-prompt"))
        assert dto is not None
        assert dto.body == "You are helpful."

    async def test_prompt_not_found_returns_none(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        q = GetPromptHandler(SqlQueryServices(session_factory))
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
        session_factory: async_sessionmaker,
    ) -> None:
        # Seed a Workflow first — NodeResult is owned by Workflow aggregate.
        from shell.domain.entities.workflow import Workflow
        from shell.domain.value_objects.ids import WorkflowId

        async with uow as u:
            await u.workflows.save(
                Workflow.new(
                    id_=WorkflowId("wf-sql-nr-1"), task_execution_id=TaskExecutionId("task-id"), now=clock.now()
                )
            )
            await u.commit()

        handler = SaveNodeResultHandler(uow, clock, id_gen)  # type: ignore[arg-type]
        await handler.handle(
            SaveNodeResultCommand(
                workflow_id="wf-sql-nr-1",
                node_id="node-sql-nr-1",
                status="done",
                stdout="success",
            )
        )

        q = GetNodeResultHandler(SqlQueryServices(session_factory))
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
        session_factory: async_sessionmaker,
    ) -> None:
        try:
            async with uow as u:
                from shell.domain.entities.prompt import Prompt
                from shell.domain.value_objects.ids import PromptId

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

        q = GetPromptHandler(SqlQueryServices(session_factory))
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
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.application.command_handlers.index_document_handler import (
            IndexDocumentHandler,
        )
        from shell.application.commands.commands import IndexDocumentCommand
        from shell.application.queries.queries import SearchSimilarQuery
        from shell.application.query_handlers.query_handlers import SearchSimilarHandler
        from shell.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        text = "SQLite RAG integration test " * 30
        cmd = IndexDocumentCommand(
            source_uri="file:///sql_rag.md", title="SQL RAG", domain="sql-test", text=text
        )
        await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(cmd)  # type: ignore[arg-type]

        results = await SearchSimilarHandler(SqlQueryServices(session_factory), embedder).handle(
            SearchSimilarQuery(query_text="SQLite RAG integration", top_k=5, domain="sql-test")
        )
        assert len(results) > 0
        assert all(r.domain == "sql-test" for r in results)

    async def test_search_domain_filter_excludes_other_domains(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.application.command_handlers.index_document_handler import (
            IndexDocumentHandler,
        )
        from shell.application.commands.commands import IndexDocumentCommand
        from shell.application.queries.queries import SearchSimilarQuery
        from shell.application.query_handlers.query_handlers import SearchSimilarHandler
        from shell.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(  # type: ignore[arg-type]
            IndexDocumentCommand(
                source_uri="file:///x.md", title="X", domain="domain-x", text="unique text x " * 20
            )
        )
        results = await SearchSimilarHandler(SqlQueryServices(session_factory), embedder).handle(
            SearchSimilarQuery(query_text="unique text x", top_k=5, domain="domain-y")
        )
        assert results == []


class TestSqlSessionRepository:
    async def test_open_append_close_and_history(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.application.command_handlers.session_handlers import (
            AppendMessageHandler,
            CloseSessionHandler,
            OpenSessionHandler,
        )
        from shell.application.commands.commands import (
            AppendMessageCommand,
            CloseSessionCommand,
            OpenSessionCommand,
        )
        from shell.application.queries.queries import GetSessionHistoryQuery
        from shell.application.query_handlers.query_handlers import GetSessionHistoryHandler

        session_id = await OpenSessionHandler(uow, clock, id_gen).handle(  # type: ignore[arg-type]
            OpenSessionCommand(goal="integration test")
        )
        await AppendMessageHandler(uow, clock, id_gen).handle(  # type: ignore[arg-type]
            AppendMessageCommand(
                session_id=session_id.value,
                correlation_id=get_correlation_id(),
                sender="sql-agent",
                receiver="router",
                payload={"k": 1},
            )
        )
        await AppendMessageHandler(uow, clock, id_gen).handle(  # type: ignore[arg-type]
            AppendMessageCommand(
                session_id=session_id.value,
                correlation_id=get_correlation_id(),
                sender="router",
                receiver="sql-agent",
                payload={"k": 2},
            )
        )
        await CloseSessionHandler(uow, clock).handle(  # type: ignore[arg-type]
            CloseSessionCommand(session_id=session_id.value)
        )

        dto = await GetSessionHistoryHandler(SqlQueryServices(session_factory)).handle(
            GetSessionHistoryQuery(session_id=session_id.value)
        )
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

        from shell.domain.events.events import TaskExecutionCreated, WorkflowStarted
        from shell.domain.value_objects.ids import TaskExecutionId, WorkflowId
        from shell.domain.value_objects.task_execution_name import TaskExecutionName
        from shell.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
        from shell.infrastructure.persistence.sql.models import AuditEventModel

        pub = SqlAuditPublisher(session_factory)
        events = [
            TaskExecutionCreated.now(
                task_execution_id=TaskExecutionId.generate(),
                task_execution_name=TaskExecutionName("audit-task"),
                now=datetime(2026, 1, 1, tzinfo=UTC),
            ),
            WorkflowStarted.now(
                workflow_id=WorkflowId.generate(),
                task_execution_id=TaskExecutionId.generate(),
                now=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        ]
        await pub.publish(events)

        async with session_factory() as session:
            rows = (await session.execute(select(AuditEventModel))).scalars().all()

        types = {r.event_type for r in rows}
        assert "TaskExecutionCreated" in types
        assert "WorkflowStarted" in types

    async def test_empty_events_writes_nothing(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
        from shell.infrastructure.persistence.sql.models import AuditEventModel

        pub = SqlAuditPublisher(session_factory)
        # record count before
        async with session_factory() as session:
            before = len((await session.execute(select(AuditEventModel))).scalars().all())
        await pub.publish([])
        async with session_factory() as session:
            after = len((await session.execute(select(AuditEventModel))).scalars().all())
        assert before == after


# ---------------------------------------------------------------------------
# SqlOutboxPublisher + OutboxToInboxRelay
# ---------------------------------------------------------------------------


class TestSqlOutboxPublisher:
    async def test_writes_outbox_rows(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell.domain.events.events import TaskExecutionCreated
        from shell.domain.value_objects.ids import TaskExecutionId
        from shell.domain.value_objects.task_execution_name import TaskExecutionName
        from shell.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell.infrastructure.persistence.sql.models import OutboxEventModel

        pub = SqlOutboxPublisher(session_factory)
        events = [
            TaskExecutionCreated.now(
                task_execution_id=TaskExecutionId.generate(),
                task_execution_name=TaskExecutionName("ob-task"),
                now=datetime(2026, 1, 1, tzinfo=UTC),
            )
        ]
        await pub.publish(events)

        async with session_factory() as session:
            rows = (await session.execute(select(OutboxEventModel))).scalars().all()
        assert any(r.event_type == "TaskExecutionCreated" for r in rows)
        assert all(r.published_at is None for r in rows)

    async def test_empty_publish_noop(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell.infrastructure.persistence.sql.models import OutboxEventModel

        pub = SqlOutboxPublisher(session_factory)
        async with session_factory() as session:
            before = len((await session.execute(select(OutboxEventModel))).scalars().all())
        await pub.publish([])
        async with session_factory() as session:
            after = len((await session.execute(select(OutboxEventModel))).scalars().all())
        assert before == after


class TestOutboxToInboxRelay:
    async def test_relay_marks_rows_published(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from sqlalchemy import select

        from shell.domain.events.events import WorkflowStarted
        from shell.domain.value_objects.ids import WorkflowId
        from shell.infrastructure.messaging.outbox_to_inbox_relay import OutboxToInboxRelay
        from shell.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell.infrastructure.persistence.memory.memory import FakeEventPublisher
        from shell.infrastructure.persistence.sql.models import OutboxEventModel

        # Write an event to outbox
        outbox_pub = SqlOutboxPublisher(session_factory)
        event = WorkflowStarted.now(
            workflow_id=WorkflowId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        await outbox_pub.publish([event])

        # Run relay — downstream captures events
        downstream = FakeEventPublisher()
        relay = OutboxToInboxRelay(session_factory, downstream)
        count = await relay.run_once()

        assert count >= 1
        async with session_factory() as session:
            rows = (
                (
                    await session.execute(
                        select(OutboxEventModel).where(OutboxEventModel.published_at.is_(None))
                    )
                )
                .scalars()
                .all()
            )
        # all rows that were pending are now published
        assert all(r.published_at is not None for r in rows)

    async def test_relay_run_twice_idempotent(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.domain.events.events import TaskExecutionCreated
        from shell.domain.value_objects.ids import TaskExecutionId
        from shell.domain.value_objects.task_execution_name import TaskExecutionName
        from shell.infrastructure.messaging.outbox_to_inbox_relay import OutboxToInboxRelay
        from shell.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell.infrastructure.persistence.memory.memory import FakeEventPublisher

        outbox_pub = SqlOutboxPublisher(session_factory)
        await outbox_pub.publish(
            [
                TaskExecutionCreated.now(
                    task_execution_id=TaskExecutionId.generate(),
                    task_execution_name=TaskExecutionName("idm-task"),
                    now=datetime(2026, 1, 1, tzinfo=UTC),
                )
            ]
        )

        downstream = FakeEventPublisher()
        relay = OutboxToInboxRelay(session_factory, downstream)
        first = await relay.run_once()
        second = await relay.run_once()

        assert first >= 1
        assert second == 0  # nothing left to process


# ---------------------------------------------------------------------------
# Transactional Outbox: atomicity guarantee
# ---------------------------------------------------------------------------


class TestTransactionalOutbox:
    async def test_outbox_written_atomically_with_domain_state(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        """Outbox rows must be present after UoW commit without a separate publish step."""
        from sqlalchemy import select

        from shell.infrastructure.persistence.sql.models import OutboxEventModel

        handler = ImportTaskExecutionHandler(uow, clock, id_gen, task_execution_loader, FakeLogger())  # type: ignore[arg-type]
        await handler.handle(ImportTaskExecutionCommand("t.md", "atomic-task"))

        async with session_factory() as session:
            rows = (
                (
                    await session.execute(
                        select(OutboxEventModel).where(OutboxEventModel.event_type == "TaskExecutionCreated")
                    )
                )
                .scalars()
                .all()
            )

        assert any(r.payload.get("task_execution_name") is not None for r in rows), (
            "Outbox row must be written in same transaction as domain state"
        )

    async def test_rollback_removes_staged_outbox_events(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        session_factory: async_sessionmaker,
    ) -> None:
        """If the UoW transaction is rolled back, no outbox rows must be written."""

        # 1. Czytelne wymuszenie i przechwycenie wyjątku za pomocą pytest
        with pytest.raises(RuntimeError, match="forced rollback"):
            async with uow as u:
                u.stage_events(
                    [
                        WorkflowStarted.now(
                            workflow_id=WorkflowId("wf-rollback"),
                            # POPRAWKA: Przekazujemy obiekt TaskExecutionId zamiast czystego stringa
                            task_execution_id=TaskExecutionId("rollback-task"),
                            now=clock.now(),
                        )
                    ]
                )
                raise RuntimeError("forced rollback")

        # 2. Bezpośrednia weryfikacja bazy — sprawdzamy tylko, czy nasz event NIE wyciekł
        async with session_factory() as session:
            result = await session.execute(select(OutboxEventModel))
            rows = result.scalars().all()

        # POPRAWKA: Wyrównanie wcięć asercji na poziomie ciała metody (po wyjściu z async with)
        assert not any(r.payload.get("workflow_id") == "wf-rollback" for r in rows), (
            "Rolled-back transaction leaked outbox rows into the DB"
        )
