"""Unit tests for application command handlers (using InMemory adapters)."""
from __future__ import annotations

import pytest

from shell.application.command_handlers.import_task_handler import ImportTaskHandler
from shell.application.command_handlers.save_node_result_handler import SaveNodeResultHandler
from shell.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell.application.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell.application.commands.commands import (
    ImportTaskCommand,
    SaveNodeResultCommand,
    SavePromptCommand,
    StartWorkflowCommand,
)
from shell.application.queries.queries import (
    GetCurrentTaskQuery,
    GetNodeResultQuery,
    GetPromptQuery,
    GetWorkflowQuery,
)
from shell.application.query_handlers.query_handlers import (
    GetCurrentTaskHandler,
    GetNodeResultHandler,
    GetPromptHandler,
    GetWorkflowHandler,
)
from shell.domain.events.events import TaskCreated, WorkflowStarted
from shell.domain.exceptions import TaskNotFound
from shell.infrastructure.logging.stdlib_logger import get_correlation_id
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
    InMemoryQueryServices,
    InMemoryUnitOfWork,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def uow() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture()
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def task_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# My Task")


@pytest.fixture()
def fake_logger() -> FakeLogger:
    return FakeLogger()


@pytest.fixture()
def queries(uow: InMemoryUnitOfWork) -> InMemoryQueryServices:
    return InMemoryQueryServices(uow)


# ---------------------------------------------------------------------------
# ImportTaskHandler
# ---------------------------------------------------------------------------


class TestImportTaskHandler:
    async def test_happy_path(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, FakeLogger())
        task_id = await handler.handle(ImportTaskCommand("t.md", "my-task"))

        assert task_id
        assert len(uow.committed_events) == 1
        assert isinstance(uow.committed_events[0], TaskCreated)

    async def test_task_saved_as_current(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, FakeLogger())
        await handler.handle(ImportTaskCommand("t.md", "my-task"))

        from shell.domain.value_objects.task_name import TaskName

        task = await uow.tasks.get_current_by_name(TaskName("my-task"))
        assert task is not None
        assert task.is_current is True

    async def test_reimport_marks_previous_non_current(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, FakeLogger())
        first_id = await handler.handle(ImportTaskCommand("t.md", "my-task"))
        await handler.handle(ImportTaskCommand("t.md", "my-task"))

        old = await uow.tasks.get_by_id(
            __import__(
                "shell.domain.value_objects.ids", fromlist=["TaskId"]
            ).TaskId(first_id)
        )
        assert old is not None
        assert old.is_current is False

    async def test_invalid_task_name_raises(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            task_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskHandler(uow, clock, id_gen, task_loader, FakeLogger())
        with pytest.raises(ValueError):
            await handler.handle(ImportTaskCommand("t.md", ""))


# ---------------------------------------------------------------------------
# StartWorkflowHandler
# ---------------------------------------------------------------------------


class TestStartWorkflowHandler:
    async def _import_task(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            task_loader: FakeTaskLoader,
    ) -> None:
        h = ImportTaskHandler(uow, clock, id_gen, task_loader, FakeLogger())
        await h.handle(ImportTaskCommand("t.md", "my-task"))
        await self._attach_graph(uow, "my-task")

    @staticmethod
    async def _attach_graph(uow: InMemoryUnitOfWork, task_name: str) -> None:
        """Persist a single-node Graph for the imported task so that
        ``StartWorkflowHandler`` can anchor the cursor on a first node.
        """
        from shell.domain.entities.graph import Graph, GraphNode
        from shell.domain.value_objects.ids import GraphId, NodeId, TemplateGraphId
        from shell.domain.value_objects.mode import Mode
        from shell.domain.value_objects.task_name import TaskName

        task = await uow.tasks.get_current_by_name(TaskName(task_name))
        assert task is not None
        graph = Graph(
            id=GraphId.generate(),
            task_id=task.id,
            template_graph_id=TemplateGraphId("tpl"),
            raw_dict={},
            nodes=[
                GraphNode(
                    id=NodeId(f"{task_name}-node-0"),
                    position=0,
                    node_dir=f"/fake/{task_name}-0",
                    mode=Mode("agent"),
                    role="agent",
                    node_type="agent",
                )
            ],
        )
        uow.graphs._store[graph.id.value] = graph

    async def test_happy_path(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            task_loader: FakeTaskLoader,
    ) -> None:
        await self._import_task(uow, clock, id_gen, task_loader)
        handler = StartWorkflowHandler(uow, clock, id_gen)
        wf_id = await handler.handle(StartWorkflowCommand("my-task"))

        assert wf_id
        assert any(isinstance(e, WorkflowStarted) for e in uow.committed_events)

    async def test_task_not_found_raises(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
    ) -> None:
        handler = StartWorkflowHandler(uow, clock, id_gen)
        with pytest.raises(TaskNotFound):
            await handler.handle(StartWorkflowCommand("nonexistent"))

    async def test_workflow_persisted(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            task_loader: FakeTaskLoader,
            queries: InMemoryQueryServices,
    ) -> None:
        await self._import_task(uow, clock, id_gen, task_loader)
        handler = StartWorkflowHandler(uow, clock, id_gen)
        wf_id = await handler.handle(StartWorkflowCommand("my-task"))

        q_handler = GetWorkflowHandler(queries)
        dto = await q_handler.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"


# ---------------------------------------------------------------------------
# SaveNodeResultHandler
# ---------------------------------------------------------------------------


class TestSaveNodeResultHandler:
    async def test_happy_path(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        from shell.domain.entities.workflow import Workflow
        from shell.domain.value_objects.ids import WorkflowId
        wf = Workflow.new(id_=WorkflowId("wf-1"), task_name="t", now=clock.now())
        uow.workflows._store["wf-1"] = wf

        handler = SaveNodeResultHandler(uow, clock, id_gen)
        result_id = await handler.handle(
            SaveNodeResultCommand(
                workflow_id="wf-1",
                node_id="node-1",
                status="done",
                stdout="ok",
            )
        )
        assert result_id
        q_handler = GetNodeResultHandler(queries)
        dto = await q_handler.handle(GetNodeResultQuery("node-1", "wf-1"))
        assert dto is not None
        assert dto.stdout == "ok"


# ---------------------------------------------------------------------------
# SavePromptHandler
# ---------------------------------------------------------------------------


class TestSavePromptHandler:
    async def test_happy_path(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("system", "You are a helpful assistant."))

        q_handler = GetPromptHandler(queries)
        dto = await q_handler.handle(GetPromptQuery("system"))
        assert dto is not None
        assert dto.body == "You are a helpful assistant."
        assert dto.is_current is True

    async def test_re_save_marks_old_non_current(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        handler = SavePromptHandler(uow, clock, id_gen)
        await handler.handle(SavePromptCommand("system", "v1"))
        await handler.handle(SavePromptCommand("system", "v2"))

        q_handler = GetPromptHandler(queries)
        dto = await q_handler.handle(GetPromptQuery("system"))
        assert dto is not None
        assert dto.body == "v2"


# ---------------------------------------------------------------------------
# QueryHandlers — not found
# ---------------------------------------------------------------------------


class TestQueryHandlersNotFound:
    async def test_get_task_not_found(self, queries: InMemoryQueryServices) -> None:
        dto = await GetCurrentTaskHandler(queries).handle(GetCurrentTaskQuery("missing"))
        assert dto is None

    async def test_get_workflow_not_found(self, queries: InMemoryQueryServices) -> None:
        dto = await GetWorkflowHandler(queries).handle(GetWorkflowQuery("no-id"))
        assert dto is None


# ---------------------------------------------------------------------------
# Faza 9: IndexDocument + Session handlers
# ---------------------------------------------------------------------------


class TestIndexDocumentHandler:
    async def test_index_and_search_returns_chunks(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        from shell.application.command_handlers.index_document_handler import (
            IndexDocumentHandler,
        )
        from shell.application.commands.commands import IndexDocumentCommand
        from shell.application.queries.queries import SearchSimilarQuery
        from shell.application.query_handlers.query_handlers import SearchSimilarHandler
        from shell.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        cmd = IndexDocumentCommand(
            source_uri="file:///doc.md",
            title="Doc",
            domain="test",
            text="Hello world " * 50,
        )
        doc_id = await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(cmd)
        assert doc_id is not None

        results = await SearchSimilarHandler(queries, embedder).handle(
            SearchSimilarQuery(query_text="Hello world", top_k=3, domain="test")
        )
        assert len(results) > 0
        assert results[0].domain == "test"

    async def test_index_empty_text_creates_no_chunks(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
    ) -> None:
        from shell.application.command_handlers.index_document_handler import (
            IndexDocumentHandler,
        )
        from shell.application.commands.commands import IndexDocumentCommand
        from shell.infrastructure.external.hash_embedder import HashEmbedder

        embedder = HashEmbedder(dim=64)
        cmd = IndexDocumentCommand(source_uri="file:///empty.md", title="Empty", domain="x", text="")
        doc_id = await IndexDocumentHandler(uow, clock, id_gen, embedder).handle(cmd)
        assert doc_id is not None
        doc = await uow.rag_documents.get_by_id(doc_id)
        assert doc is not None
        assert doc.chunks == []


class TestSessionHandlers:
    async def test_open_and_get_history(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        from shell.application.command_handlers.session_handlers import (
            AppendMessageHandler,
            OpenSessionHandler,
        )
        from shell.application.commands.commands import AppendMessageCommand, OpenSessionCommand
        from shell.application.queries.queries import GetSessionHistoryQuery
        from shell.application.query_handlers.query_handlers import GetSessionHistoryHandler

        session_id = await OpenSessionHandler(uow, clock, id_gen).handle(
            OpenSessionCommand(goal="do work")
        )
        await AppendMessageHandler(uow, clock, id_gen).handle(
            AppendMessageCommand(session_id=session_id.value,correlation_id=get_correlation_id(), sender="agent-1", receiver="router", payload={"x": 1})
        )
        dto = await GetSessionHistoryHandler(queries).handle(GetSessionHistoryQuery(session_id=session_id.value))
        assert dto is not None
        assert dto.status == "open"
        assert len(dto.messages) == 1

    async def test_close_session(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
            id_gen: FakeIdGenerator,
            queries: InMemoryQueryServices,
    ) -> None:
        from shell.application.command_handlers.session_handlers import (
            CloseSessionHandler,
            OpenSessionHandler,
        )
        from shell.application.commands.commands import CloseSessionCommand, OpenSessionCommand
        from shell.application.queries.queries import GetSessionHistoryQuery
        from shell.application.query_handlers.query_handlers import GetSessionHistoryHandler

        session_id = await OpenSessionHandler(uow, clock, id_gen).handle(
            OpenSessionCommand(goal="close test")
        )
        await CloseSessionHandler(uow, clock).handle(CloseSessionCommand(session_id=session_id.value))
        dto = await GetSessionHistoryHandler(queries).handle(GetSessionHistoryQuery(session_id=session_id.value))
        assert dto is not None
        assert dto.status == "closed"

    async def test_close_not_found_raises(
            self,
            uow: InMemoryUnitOfWork,
            clock: FakeClock,
    ) -> None:
        from shell.application.command_handlers.session_handlers import (
            CloseSessionHandler,
            SessionNotFound,
        )
        from shell.application.commands.commands import CloseSessionCommand

        with pytest.raises(SessionNotFound):
            await CloseSessionHandler(uow, clock).handle(CloseSessionCommand(session_id="no-such-id"))

    async def test_get_history_not_found_returns_none(self, queries: InMemoryQueryServices) -> None:
        from shell.application.queries.queries import GetSessionHistoryQuery
        from shell.application.query_handlers.query_handlers import GetSessionHistoryHandler

        dto = await GetSessionHistoryHandler(queries).handle(GetSessionHistoryQuery(session_id="ghost"))
        assert dto is None
