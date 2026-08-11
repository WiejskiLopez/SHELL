"""SqlAlchemyUnitOfWorkBase — wspólna logika cyklu życia transakcji dla per-BC UoW.

Każdy BC dziedziczy tę klasę i nadpisuje wyłącznie metodę ``_build_repo_map()``
zwracając słownik {DomainPort -> SqlAdapter} dla własnych agregatów.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy.orm.exc import StaleDataError

from shell.platform.application.ports.unit_of_work import UnitOfWork
from shell.platform.domain.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.platform.infrastructure.context import get_causation_id, get_correlation_id
from shell.platform.infrastructure.persistence.sql.models import AuditEventModel, OutboxEventModel
from shell.platform.infrastructure.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.domain.events import DomainEvent

TRepository = TypeVar("TRepository")


class SqlAlchemyUnitOfWorkBase(UnitOfWork):
    """Bazowa klasa UoW — zarządza sesją, outboxem i transakcjami.

    Podklasy nadpisują ``_build_repo_map()`` by zadeklarować
    wyłącznie repozytoria swojego BC.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        mapper: Any | None = None,
    ) -> None:
        self._factory = session_factory
        self._mapper = mapper
        self._staged_events: list[DomainEvent] = []
        self._staged_messages: list[object] = []
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
            return sql_type(self._active_session)  # type: ignore[no-any-return]
        msg = f"Unknown repository type for this BC: {repo_type.__name__}"
        raise ValueError(msg)

    def stage_events(self, events: Sequence[object]) -> None:
        self._staged_events.extend(events)  # type: ignore[arg-type]

    def stage_messages(self, messages: list[object]) -> None:
        self._staged_messages.extend(messages)

    async def save(self, repo_type: type, aggregate: object) -> None:
        repo: Any = self.repository(repo_type)
        await repo.save(aggregate)
        domain_events = aggregate.pull_events()  # type: ignore[attr-defined]
        if self._mapper is not None:
            mapped = [self._mapper.map(e) for e in domain_events]
            self.stage_events(mapped)
        else:
            self.stage_events(domain_events)

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
                raw_occurred_at = (
                    event.occurred_at.value
                    if hasattr(event.occurred_at, "value")
                    else event.occurred_at
                )
                event_type = type(event).__name__
                payload = serializer.to_payload(event)
                outbox = OutboxEventModel(
                    id=str(uuid.uuid4()),
                    event_type=event_type,
                    occurred_at=raw_occurred_at,
                    payload=payload,
                    correlation_id=get_correlation_id(),
                    causation_id=get_causation_id(),
                )
                self._session.add(outbox)
                self._session.add(
                    AuditEventModel(
                        id=str(uuid.uuid4()),
                        event_type=event_type,
                        occurred_at=raw_occurred_at,
                        payload=payload,
                    )
                )

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
