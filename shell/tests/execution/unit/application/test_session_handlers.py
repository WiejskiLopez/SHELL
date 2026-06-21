"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

import pytest
from shell.application.execution.command_handlers.session_handlers import (
    AppendMessageHandler,
    CloseSessionHandler,
    OpenSessionHandler,
    SessionNotFound,
)
from shell.application.platform.commands.commands import (
    AppendMessageCommand,
    CloseSessionCommand,
    OpenSessionCommand,
)
from shell.application.platform.queries.queries import GetSessionHistoryQuery
from shell.application.platform.query_handlers.query_handlers import GetSessionHistoryHandler
from shell.infrastructure.platform.logging.stdlib_logger import get_correlation_id
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    InMemoryQueryServices,
    InMemoryUnitOfWork,
)


class TestSessionHandlers:
    async def test_open_and_get_history(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        queries: InMemoryQueryServices,
    ) -> None:
        session_id = await OpenSessionHandler(uow, clock, id_gen).handle(
            OpenSessionCommand(goal="do work")
        )
        await AppendMessageHandler(uow, clock, id_gen).handle(
            AppendMessageCommand(
                session_id=session_id.value,
                correlation_id=get_correlation_id(),
                sender="agent-1",
                receiver="router",
                payload={"x": 1},
            )
        )
        dto = await GetSessionHistoryHandler(queries).handle(
            GetSessionHistoryQuery(session_id=session_id.value)
        )
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
        session_id = await OpenSessionHandler(uow, clock, id_gen).handle(
            OpenSessionCommand(goal="close test")
        )
        await CloseSessionHandler(uow, clock).handle(
            CloseSessionCommand(session_id=session_id.value)
        )
        dto = await GetSessionHistoryHandler(queries).handle(
            GetSessionHistoryQuery(session_id=session_id.value)
        )
        assert dto is not None
        assert dto.status == "closed"

    async def test_close_not_found_raises(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SessionNotFound):
            await CloseSessionHandler(uow, clock).handle(
                CloseSessionCommand(session_id="no-such-id")
            )

    async def test_get_history_not_found_returns_none(self, queries: InMemoryQueryServices) -> None:
        dto = await GetSessionHistoryHandler(queries).handle(
            GetSessionHistoryQuery(session_id="ghost")
        )
        assert dto is None
