"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.session_service.application.session.session.command_handlers.close_session_handler import (
    CloseSessionHandler,
)
from shell.session_service.application.session.session.command_handlers.open_session_handler import (
    OpenSessionHandler,
)
from shell.session_service.application.session.session.commands import (
    CloseSessionCommand,
    OpenSessionCommand,
)
from shell.session_service.application.session.session.exceptions.session_not_found import (
    SessionNotFound,
)
from shell.session_service.application.session.session.queries.get_session_history_query import (
    GetSessionHistoryQuery,
)
from shell.session_service.application.session.session.query_handlers.get_session_history_handler import (
    GetSessionHistoryHandler,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.persistence.memory import (
        FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
        FakeIdGenerator,  # noqa: TC002 — FakeIdGenerator używany w sygnaturach fixture'ów pytest
    )
    from shell.session_service.infrastructure.session.persistence.memory.query_services import (
        InMemorySessionQueryService,  # noqa: TC002 — używany w sygnaturach fixture'ów pytest
    )
    from shell.session_service.infrastructure.session.persistence.memory.unit_of_work import (
        InMemorySessionUnitOfWork,  # noqa: TC002 — używany w sygnaturach fixture'ów pytest
    )


class TestSessionHandlers:
    async def test_open_and_get_history(
        self,
        unit_of_work: InMemorySessionUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        queries: InMemorySessionQueryService,
    ) -> None:
        session_id = await OpenSessionHandler(unit_of_work, clock, id_generator).handle(
            OpenSessionCommand(user_id="user-1")
        )
        dto = await GetSessionHistoryHandler(queries).handle(
            GetSessionHistoryQuery(session_id=session_id.value)
        )
        assert dto is not None
        assert dto.status == "OPEN"

    async def test_close_session(
        self,
        unit_of_work: InMemorySessionUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        queries: InMemorySessionQueryService,
    ) -> None:
        session_id = await OpenSessionHandler(unit_of_work, clock, id_generator).handle(
            OpenSessionCommand(user_id="user-1")
        )
        await CloseSessionHandler(unit_of_work, clock).handle(
            CloseSessionCommand(session_id=session_id.value)
        )
        dto = await GetSessionHistoryHandler(queries).handle(
            GetSessionHistoryQuery(session_id=session_id.value)
        )
        assert dto is not None
        assert dto.status == "CLOSED"

    async def test_close_not_found_raises(
        self,
        unit_of_work: InMemorySessionUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SessionNotFound):
            await CloseSessionHandler(unit_of_work, clock).handle(
                CloseSessionCommand(session_id="no-such-id")
            )

    async def test_get_history_not_found_returns_none(
        self, queries: InMemorySessionQueryService
    ) -> None:
        dto = await GetSessionHistoryHandler(queries).handle(
            GetSessionHistoryQuery(session_id="ghost")
        )
        assert dto is None
