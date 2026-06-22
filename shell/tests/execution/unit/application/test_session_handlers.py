"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

import pytest
from shell.application.execution.command_handlers.session_handlers import (
    CloseSessionHandler,
    OpenSessionHandler,
    SessionNotFound,
)
from shell.application.platform.commands.commands import (
    CloseSessionCommand,
    OpenSessionCommand,
)
from shell.application.platform.queries.queries import GetSessionHistoryQuery
from shell.application.platform.query_handlers.query_handlers import GetSessionHistoryHandler
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
    FakeIdGenerator,  # noqa: TC002 — FakeIdGenerator używany w sygnaturach fixture'ów pytest
    InMemoryQueryServices,  # noqa: TC002 — InMemoryQueryServices używany w sygnaturach fixture'ów pytest
    InMemoryUnitOfWork,  # noqa: TC002 — InMemoryUnitOfWork używany w sygnaturach fixture'ów pytest
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
        dto = await GetSessionHistoryHandler(queries).handle(
            GetSessionHistoryQuery(session_id=session_id.value)
        )
        assert dto is not None
        assert dto.status == "open"

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
