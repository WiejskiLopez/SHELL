"""SqlAlchemyUnitOfWorkBase — wspólna logika cyklu życia transakcji dla per-BC UoW.

Każdy BC dziedziczy tę klasę i nadpisuje wyłącznie metodę ``_build_repo_map()``
zwracając słownik {DomainPort -> SqlAdapter} dla własnych agregatów.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from sqlalchemy.orm.exc import StaleDataError

from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
from shell.platform.domain.events import DomainEvent
from shell.platform.domain.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.platform.infrastructure.context import (
    get_session_scope,
)
from shell.platform.infrastructure.messaging.transport.source_service import (
    source_service_for_type,
)
from shell.platform.infrastructure.serialization.event.integration_event_serializer import (
    IntegrationEventSerializer,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.ports.technical_id_generator import TechnicalIdGenerator
    from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
        PersistenceDeliveryModels,
    )


class SqlAlchemyUnitOfWorkBase(UnitOfWork):
    """Bazowa klasa UoW — zarządza sesją, outboxem i transakcjami.

    Podklasy nadpisują ``_build_repo_map()`` by zadeklarować
    wyłącznie repozytoria swojego BC.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        mapper: Any,
        models: PersistenceDeliveryModels | None = None,
        id_generator: TechnicalIdGenerator | None = None,
    ) -> None:
        if models is None:
            raise ValueError("SqlAlchemyUnitOfWorkBase requires a persistence delivery bundle")
        if mapper is None:
            raise ValueError("SqlAlchemyUnitOfWorkBase requires an integration mapper")
        self._factory = session_factory
        self._mapper = mapper
        self._models = models
        from shell.platform.infrastructure.identity.uuid_technical_id_generator import (
            UuidTechnicalIdGenerator,
        )

        self._id_generator = id_generator or UuidTechnicalIdGenerator()
        self._staged_events: list[DomainEvent] = []
        self._staged_messages: list[object] = []
        self._committed = False
        self._deferred_commit = False
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

    def repository(self, repo_type: type[Any]) -> Any:
        repo_map = self._build_repo_map()
        sql_type = repo_map.get(repo_type)
        if sql_type is not None:
            return sql_type(self._active_session)
        msg = f"Unknown repository type for this BC: {repo_type.__name__}"
        raise ValueError(msg)

    def stage_events(self, events: Sequence[object]) -> None:
        invalid = [event for event in events if not isinstance(event, DomainEvent)]
        if invalid:
            raise TypeError("SqlAlchemyUnitOfWorkBase stages DomainEvent instances only")
        self._staged_events.extend(cast("Sequence[DomainEvent]", events))

    def stage_messages(self, messages: list[object]) -> None:
        self._staged_messages.extend(messages)

    async def save(self, repo_type: type, aggregate: object) -> None:
        repo: Any = self.repository(repo_type)
        await repo.save(aggregate)
        domain_events = aggregate.pull_events()  # type: ignore[attr-defined]
        self.stage_events(domain_events)

    async def __aenter__(self) -> SqlAlchemyUnitOfWorkBase:
        scope = get_session_scope()
        if scope is not None:
            # Delivery processor owns the transaction: reuse its session and
            # defer the commit so business change + outbox + inbox ack are one.
            self._session = scope.session
            self._deferred_commit = True
        else:
            self._session = self._factory()
            await self._session.__aenter__()
            self._deferred_commit = False
        self._committed = False
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._session is not None:
            exc_type = args[0] if args else None
            if exc_type is None and not self._committed:
                # In deferred mode commit() only writes the outbox rows and
                # flushes — the real DB commit belongs to the processor.
                await self.commit()
            if not self._deferred_commit:
                await self._session.__aexit__(*args)
            self._session = None

    async def commit(self) -> None:
        if self._session is None:
            return
        try:
            await self._write_staged_outbox()
            if self._deferred_commit:
                # Materialize the pending changes in the shared transaction;
                # the actual commit belongs to the processor.
                await self._session.flush()
            else:
                await self._session.commit()
            self._staged_events.clear()
            self._staged_messages.clear()
            self._committed = True
        except StaleDataError as exc:
            await self._session.rollback()
            raise ConcurrentModificationError("Aggregate", str(exc)) from exc

    async def _write_staged_outbox(self) -> None:
        if self._session is None:
            return
        serializer = IntegrationEventSerializer()
        for domain_event in self._staged_events:
            integration_event = self._mapper.map(domain_event)
            envelope = serializer.to_envelope(
                integration_event,
                outbox_id=self._id_generator.new_id(),
                source_service=source_service_for_type(type(domain_event)),
            )
            outbox = self._models.events.outbox(
                id=envelope["outbox_id"],
                event_id=envelope["event_id"],
                source_service=envelope["source_service"],
                event_type=envelope["event_type"],
                occurred_at=envelope["occurred_at"],
                aggregate_id=envelope["aggregate_id"],
                aggregate_name=envelope["aggregate_name"],
                schema_version=envelope["schema_version"],
                payload=envelope["payload"],
                correlation_id=envelope["correlation_id"],
                causation_id=envelope["causation_id"],
            )
            self._session.add(outbox)
            self._session.add(
                self._models.audit(
                    id=self._id_generator.new_id(),
                    event_type=envelope["event_type"],
                    occurred_at=envelope["occurred_at"],
                    payload=envelope["payload"],
                )
            )

    async def rollback(self) -> None:
        if self._session is not None:
            await self._session.rollback()
        self._staged_events.clear()
        self._staged_messages.clear()
        if self._deferred_commit:
            scope = get_session_scope()
            if scope is not None:
                scope.rolled_back = True
