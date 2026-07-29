"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.application.session.session.command_handlers.close_session_handler import (
    CloseSessionHandler,
)
from shell.application.session.session.command_handlers.open_session_handler import (
    OpenSessionHandler,
)
from shell.application.session.session.commands import (
    CloseSessionCommand,
    OpenSessionCommand,
)
from shell.application.session.session.exceptions.session_not_found import SessionNotFound
from shell.application.session.session.queries.get_session_history_query import (
    GetSessionHistoryQuery,
)
from shell.application.session.session.query_handlers.get_session_history_handler import (
    GetSessionHistoryHandler,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.persistence.memory import (
        FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
        FakeIdGenerator,  # noqa: TC002 — FakeIdGenerator używany w sygnaturach fixture'ów pytest
        InMemoryQueryServices,  # noqa: TC002 — InMemoryQueryServices używany w sygnaturach fixture'ów pytest
        InMemoryUnitOfWork,  # noqa: TC002 — InMemoryUnitOfWork używany w sygnaturach fixture'ów pytest
    )


class TestSessionHandlers:
    async def test_open_and_get_history(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        queries: InMemoryQueryServices,
    ) -> None:
        session_id = await OpenSessionHandler(unit_of_work, clock, id_generator).handle(
            OpenSessionCommand(goal="do work")
        )
        dto = await GetSessionHistoryHandler(queries).handle(  # type: ignore[arg-type]
            GetSessionHistoryQuery(session_id=session_id.value)
        )
        assert dto is not None
        assert dto.status == "open"

    async def test_close_session(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        queries: InMemoryQueryServices,
    ) -> None:
        session_id = await OpenSessionHandler(unit_of_work, clock, id_generator).handle(
            OpenSessionCommand(goal="close test")
        )
        await CloseSessionHandler(unit_of_work, clock).handle(
            CloseSessionCommand(session_id=session_id.value)
        )
        dto = await GetSessionHistoryHandler(queries).handle(  # type: ignore[arg-type]
            GetSessionHistoryQuery(session_id=session_id.value)
        )
        assert dto is not None
        assert dto.status == "closed"

    async def test_close_not_found_raises(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SessionNotFound):
            await CloseSessionHandler(unit_of_work, clock).handle(
                CloseSessionCommand(session_id="no-such-id")
            )

    async def test_get_history_not_found_returns_none(self, queries: InMemoryQueryServices) -> None:
        dto = await GetSessionHistoryHandler(queries).handle(  # type: ignore[arg-type]
            GetSessionHistoryQuery(session_id="ghost")
        )
        assert dto is None
