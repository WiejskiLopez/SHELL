"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.application.execution.session_execution.commands import (
    CloseSessionCommand,
    OpenSessionCommand,
)
from shell.application.execution.session_execution.queries.session_get_history_query import (
    SessionGetHistoryQuery,
)
from shell.application.execution.session_execution.query_handlers.session_get_history_handler import (
    SessionGetHistoryHandler,
)
from shell.application.session.session.command_handlers.session_close_handler import (
    SessionCloseHandler,
)
from shell.application.session.session.command_handlers.session_open_handler import (
    SessionOpenHandler,
)
from shell.application.session.session.exceptions.session_not_found import SessionNotFound

if TYPE_CHECKING:
    from shell.infrastructure.platform.persistence.memory import (
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
        session_id = await SessionOpenHandler(unit_of_work, clock, id_generator).handle(
            OpenSessionCommand(goal="do work")
        )
        dto = await SessionGetHistoryHandler(queries).handle(  # type: ignore[arg-type]
            SessionGetHistoryQuery(session_id=session_id.value)
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
        session_id = await SessionOpenHandler(unit_of_work, clock, id_generator).handle(
            OpenSessionCommand(goal="close test")
        )
        await SessionCloseHandler(unit_of_work, clock).handle(
            CloseSessionCommand(session_id=session_id.value)
        )
        dto = await SessionGetHistoryHandler(queries).handle(  # type: ignore[arg-type]
            SessionGetHistoryQuery(session_id=session_id.value)
        )
        assert dto is not None
        assert dto.status == "closed"

    async def test_close_not_found_raises(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SessionNotFound):
            await SessionCloseHandler(unit_of_work, clock).handle(
                CloseSessionCommand(session_id="no-such-id")
            )

    async def test_get_history_not_found_returns_none(self, queries: InMemoryQueryServices) -> None:
        dto = await SessionGetHistoryHandler(queries).handle(  # type: ignore[arg-type]
            SessionGetHistoryQuery(session_id="ghost")
        )
        assert dto is None
