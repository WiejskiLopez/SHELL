"""SqlAlchemyUnitOfWorkBase — wspólna logika cyklu życia transakcji dla per-BC UoW.

Każdy BC dziedziczy tę klasę i nadpisuje wyłącznie metodę ``_build_repo_map()``
zwracając słownik {DomainPort -> SqlAdapter} dla własnych agregatów.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy.orm.exc import StaleDataError

from shell.application.platform.ports.unit_of_work import UnitOfWork
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.infrastructure.platform.context import get_causation_id, get_correlation_id
from shell.infrastructure.platform.persistence.sql.models import OutboxEventModel
from shell.infrastructure.platform.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.domain.messaging.aggregates.message.message import Message
    from shell.domain.platform.events import DomainEvent

TRepository = TypeVar("TRepository")


class SqlAlchemyUnitOfWorkBase(UnitOfWork):
    """Bazowa klasa UoW — zarządza sesją, outboxem i transakcjami.

    Podklasy nadpisują ``_build_repo_map()`` by zadeklarować
    wyłącznie repozytoria swojego BC.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory
        self._staged_events: list[DomainEvent] = []
        self._staged_messages: list[Message] = []
        self._committed = False
        self._session: AsyncSession | None = None

    # ------------------------------------------------------------------
    # Metoda do nadpisania przez podklasy
    # ------------------------------------------------------------------

    def _build_repo_map(self) -> dict[type, type]:
        """Zwraca mapę {DomainRepo -> SqlRepo} dla tego BC.

        Podklasa MUSI nadpisać tę metodę.
        """
        return {}

    # ------------------------------------------------------------------
    # UnitOfWork Protocol
    # ------------------------------------------------------------------

    @property
    def _active_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork not entered; use 'async with'")
        return self._session

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    def repository(self, repo_type: type[TRepository]) -> TRepository:
        repo_map = self._build_repo_map()
        sql_type = repo_map.get(repo_type)
        if sql_type is not None:
            return sql_type(self._active_session)
        msg = f"Unknown repository type for this BC: {repo_type.__name__}"
        raise ValueError(msg)

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._staged_events.extend(events)

    def stage_messages(self, messages: list[Message]) -> None:
        self._staged_messages.extend(messages)

    async def save(self, repo_type: type, aggregate: Any) -> None:
        repo: Any = self.repository(repo_type)
        await repo.save(aggregate)
        self.stage_events(aggregate.pull_events())

    async def __aenter__(self) -> SqlAlchemyUnitOfWorkBase:
        self._session = self._factory()
        await self._session.__aenter__()
        self._committed = False
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._session is not None:
            exc_type = args[0] if args else None
            if exc_type is None and not self._committed:
                await self.commit()
            await self._session.__aexit__(*args)
            self._session = None

    async def commit(self) -> None:
        if self._session is None:
            return
        try:
            serializer = DomainEventSerializer()
            for event in self._staged_events:
                outbox = OutboxEventModel(
                    id=str(uuid.uuid4()),
                    event_type=type(event).__name__,
                    occurred_at=event.occurred_at.value,
                    payload=serializer.to_payload(event),
                    correlation_id=get_correlation_id(),
                    causation_id=get_causation_id(),
                )
                self._session.add(outbox)

            await self._session.commit()
            self._staged_events.clear()
            self._staged_messages.clear()
            self._committed = True
        except StaleDataError as exc:
            await self._session.rollback()
            raise ConcurrentModificationError("Aggregate", str(exc)) from exc

    async def rollback(self) -> None:
        if self._session is not None:
            await self._session.rollback()
        self._staged_events.clear()
        self._staged_messages.clear()
