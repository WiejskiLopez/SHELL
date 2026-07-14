from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import text

from shell.platform.infrastructure.context import (
    causation_id_var,
    correlation_id_var,
)
from shell.platform.infrastructure.messaging.serialization.command_deserializer import (
    CommandDeserializer,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.application.bus.command_bus import CommandBus


class CommandInboxProcessor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        command_bus: CommandBus,
        batch_size: int = 100,
        registry: dict[str, type[object]] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._command_bus = command_bus
        self._batch_size = batch_size
        self._deserializer = CommandDeserializer(registry=registry)  # type: ignore[arg-type]

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    text("""
                        SELECT id, command_type, occurred_at, payload, correlation_id, causation_id
                        FROM inbox_command
                        WHERE processed_at IS NULL
                        LIMIT :limit
                        FOR UPDATE SKIP LOCKED
                    """),
                    {"limit": self._batch_size},
                )
            ).all()

            if not rows:
                return 0

            now = datetime.now(UTC)
            ids = []
            for row in rows:
                command = self._deserializer.deserialize(
                    command_type=row.command_type,
                    payload=row.payload,
                )
                if command is not None:
                    corr_token = correlation_id_var.set(row.correlation_id)
                    caus_token = causation_id_var.set(row.causation_id)
                    try:
                        await self._command_bus.dispatch(command)
                    finally:
                        correlation_id_var.reset(corr_token)
                        causation_id_var.reset(caus_token)
                ids.append(row.id)

            await session.execute(
                text("UPDATE inbox_command SET processed_at = :now WHERE id = ANY(:ids)"),
                {"now": now, "ids": ids},
            )
            await session.commit()
            return len(rows)
