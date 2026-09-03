"""CommandOutboxRelay — reads pending ``outbox_command`` rows and publishes via the command transport."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol, cast

from sqlalchemy import select

from shell.platform.application.ports.transport.command_transport import (
    CommandDeliveryEnvelope,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy.orm import Mapped

    from shell.platform.application.ports.transport.command_transport import (
        CommandDeliveryTransport,
    )
    from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
        CommandDeliveryModels,
    )


class CommandOutboxModel(Protocol):
    id: Mapped[str]
    command_id: Mapped[str]
    command_name: Mapped[str]
    source_service: Mapped[str]
    target_service: Mapped[str]
    schema_version: Mapped[int]
    issued_at: Mapped[datetime]
    payload: Mapped[dict[str, object]]
    correlation_id: Mapped[str]
    causation_id: Mapped[str]
    published_at: Mapped[datetime | None]


class CommandOutboxRow(Protocol):
    id: str
    command_id: str
    command_name: str
    source_service: str
    target_service: str
    schema_version: int
    issued_at: datetime
    payload: dict[str, object]
    correlation_id: str
    causation_id: str
    published_at: datetime | None


class CommandOutboxToTransportRelay:
    """Publishes pending command outbox rows and marks them published on success."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        models: CommandDeliveryModels,
        transport: CommandDeliveryTransport,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._outbox_model = cast("type[CommandOutboxModel]", models.outbox)
        self._transport = transport
        self._batch_size = batch_size

        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            stmt = (
                select(self._outbox_model)
                .where(self._outbox_model.published_at.is_(None))
                .order_by(self._outbox_model.issued_at)
                .limit(self._batch_size)
            )
            if self._skip_locked:
                stmt = stmt.with_for_update(skip_locked=True)

            rows = (await session.execute(stmt)).scalars().all()
            if not rows:
                return 0

            now = datetime.now(tz=UTC)
            envelopes = [self._to_envelope(row) for row in rows]
            for envelope in envelopes:
                await self._transport.deliver(envelope)

            for row in rows:
                cast("CommandOutboxRow", row).published_at = now
            await session.commit()
            return len(rows)

    def _to_envelope(self, row: object) -> CommandDeliveryEnvelope:
        command_row = cast("CommandOutboxRow", row)
        return CommandDeliveryEnvelope(
            kind="command",
            outbox_id=command_row.id,
            command_id=command_row.command_id,
            command_name=command_row.command_name,
            source_service=command_row.source_service,
            target_service=command_row.target_service,
            issued_at=command_row.issued_at,
            payload=command_row.payload,
            correlation_id=command_row.correlation_id,
            causation_id=command_row.causation_id,
            schema_version=command_row.schema_version,
        )