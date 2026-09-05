"""OutboxRelayBase — wspólny cykl publikacji outbox → transport.

Relay'e eventu i komendy dzielą ten sam cykl operacyjny: wybór rekordów
oczekujących (``published_at IS NULL``), zbudowanie kopert, dostawa do brokera,
oznaczenie rekordów jako opublikowane i commit. Baza posiada ten cykl;
podklasy dostarczają wyłącznie części zależne od kanału: model outboxa,
kolumnę porządkującą i fabrykę koperty.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class OutboxRelayBase(ABC):
    """Publishes pending outbox rows and marks them published on success."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        transport: Any,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._transport = transport
        self._batch_size = batch_size

        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)

    @property
    @abstractmethod
    def outbox_model(self) -> type[Any]:
        """Model ORM tabeli outbox dla danego kanału."""

    @property
    @abstractmethod
    def order_column(self) -> Any:
        """Kolumna porządkująca rekordy oczekujące (per kanał)."""

    @abstractmethod
    def _to_envelope(self, row: object) -> object:
        """Buduje kopertę delivery właściwą dla kanału z wiersza outbox."""

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            stmt = (
                select(self.outbox_model)
                .where(self.outbox_model.published_at.is_(None))
                .order_by(self.order_column)
                .limit(self._batch_size)
            )
            if self._skip_locked:
                stmt = stmt.with_for_update(skip_locked=True)

            rows = (await session.execute(stmt)).scalars().all()
            if not rows:
                return 0

            now = datetime.now(tz=UTC)
            for envelope in (self._to_envelope(row) for row in rows):
                await self._transport.deliver(envelope)

            for row in rows:
                row.published_at = now
            await session.commit()
            return len(rows)